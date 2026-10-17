import os
import shutil
import uuid
import tempfile
import re
import pandas as pd
import fitz  # PyMuPDF
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from .jobs import run_in_background
from .office_utils import convert_office_to_pdf

try:
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    pass

router = APIRouter()
TEMP_DIR = os.path.join(tempfile.gettempdir(), "pdf_tools")
os.makedirs(TEMP_DIR, exist_ok=True)


def _do_pdf_to_excel(job_dir: str, temp_path: str, original_filename: str) -> dict:
    """Convert PDF to Excel preserving all text, tables, and column alignments."""
    output_filename = original_filename.rsplit(".", 1)[0] + ".xlsx"
    output_path = os.path.join(job_dir, output_filename)

    from openpyxl import Workbook

    wb = Workbook()
    # Remove default sheet
    default_sheet = wb.active

    has_data = False
    all_dfs = []

    with fitz.open(temp_path) as doc:
        for page_idx, page in enumerate(doc):
            page_tables = []
            try:
                tables = page.find_tables()
                for tab in tables:
                    df = tab.to_pandas()
                    if not df.empty:
                        page_tables.append(df)
            except Exception as e:
                print(f"find_tables warning on page {page_idx}: {e}")

            if page_tables:
                for t_idx, df in enumerate(page_tables):
                    sheet_name = f"P{page_idx + 1}_Table{t_idx + 1}"[:31]
                    ws = wb.create_sheet(title=sheet_name)
                    # Write header
                    ws.append(list(df.columns))
                    # Write rows
                    for row in df.itertuples(index=False):
                        ws.append(list(row))
                    has_data = True
            else:
                # Extract text preserving column structures (tabs or multi-spaces)
                text = page.get_text("text")
                if text.strip():
                    sheet_name = f"Page_{page_idx + 1}"[:31]
                    ws = wb.create_sheet(title=sheet_name)
                    for line in text.splitlines():
                        line_stripped = line.strip()
                        if not line_stripped:
                            continue
                        # Split by tabs or 2+ consecutive spaces for tabular columns
                        cols = [c.strip() for c in re.split(r"\t| {2,}", line_stripped) if c.strip()]
                        ws.append(cols if cols else [line_stripped])
                    has_data = True

    if not has_data:
        ws = wb.create_sheet(title="Content")
        ws.append(["No content detected in PDF."])

    # Remove the initial blank sheet if other sheets were created
    if default_sheet in wb.worksheets and len(wb.worksheets) > 1:
        wb.remove(default_sheet)

    wb.save(output_path)

    return {
        "output_path": output_path,
        "filename": output_filename,
        "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }


def _do_excel_to_pdf(job_dir: str, temp_path: str, original_filename: str) -> dict:
    """Convert Excel (.xls, .xlsx) to PDF using LibreOffice headless.
    Preserves exact sheet layout, formulas, fonts, and colors, finishing in ~1-2s.
    Falls back to ReportLab if LibreOffice is unavailable.
    """
    output_filename = original_filename.rsplit(".", 1)[0] + ".pdf"
    expected_output = os.path.join(job_dir, output_filename)

    # 1. Primary: LibreOffice headless calc export
    try:
        pdf_path = convert_office_to_pdf(temp_path, job_dir, timeout=30)
        if pdf_path != expected_output and os.path.exists(pdf_path):
            if os.path.exists(expected_output):
                os.remove(expected_output)
            os.rename(pdf_path, expected_output)
            pdf_path = expected_output

        return {
            "output_path": pdf_path,
            "filename": output_filename,
            "media_type": "application/pdf",
        }
    except Exception as e:
        print(f"LibreOffice excel-to-pdf failed: {e}, falling back to ReportLab...")

    # 2. Fallback: ReportLab rendering
    xls = pd.ExcelFile(temp_path)
    doc = SimpleDocTemplate(expected_output, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        elements.append(Paragraph(f"Sheet: {sheet_name}", styles["Heading2"]))
        elements.append(Spacer(1, 12))
        table_data = [df.columns.tolist()] + df.astype(str).values.tolist()
        t = Table(table_data)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 24))

    doc.build(elements)
    return {
        "output_path": expected_output,
        "filename": output_filename,
        "media_type": "application/pdf",
    }


@router.post("/pdf-to-excel")
async def pdf_to_excel(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    temp_path = os.path.join(job_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    run_in_background(job_id, _do_pdf_to_excel, job_dir, temp_path, file.filename)
    return JSONResponse(content={"job_id": job_id, "status": "processing"})


@router.post("/excel-to-pdf")
async def excel_to_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="File must be an Excel document (.xls or .xlsx).")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    temp_path = os.path.join(job_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    run_in_background(job_id, _do_excel_to_pdf, job_dir, temp_path, file.filename)
    return JSONResponse(content={"job_id": job_id, "status": "processing"})
