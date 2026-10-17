import os
import shutil
import uuid
import tempfile
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from .jobs import run_in_background
from .office_utils import convert_office_to_pdf

try:
    import pdf2docx.text.Spans
    from pdf2docx.text.TextSpan import TextSpan
    from pdf2docx.image.ImageSpan import ImageSpan
    from pdf2docx import Converter

    def _safe_spans_restore(self, raws: list):
        for raw_span in raws:
            if "image" in raw_span:
                span = ImageSpan(raw_span)
            else:
                span = TextSpan(raw_span)
                # Keep whitespace spans so word spacing is never lost
                if not span.text:
                    span = None
            self.append(span)
        return self

    pdf2docx.text.Spans.Spans.restore = _safe_spans_restore
except Exception:
    Converter = None

router = APIRouter()
TEMP_DIR = os.path.join(tempfile.gettempdir(), "pdf_tools")
os.makedirs(TEMP_DIR, exist_ok=True)


from .layout_converter import (
    detect_page_columns,
    render_multicolumn_document,
    clean_docx_typography,
)
import fitz
import docx


def _do_pdf_to_word(job_dir: str, temp_path: str, input_filename: str) -> dict:
    """Convert PDF to Word with layout intelligence:
    - Multi-column documents (resumes, challans) are rendered with strict column separation.
    - Single-column/tabular documents use pdf2docx with stream-table protection.
    - Headings with artificial PDF letter-spacing are automatically normalized.
    """
    output_filename = input_filename.rsplit(".", 1)[0] + ".docx"
    output_path = os.path.join(job_dir, output_filename)

    has_multi_column = False
    total_pdf_chars = 0
    with fitz.open(temp_path) as doc_fitz:
        for page in doc_fitz:
            cols = detect_page_columns(page)
            if len(cols) >= 2:
                has_multi_column = True
            total_pdf_chars += len(page.get_text("text").strip())

    if has_multi_column:
        render_multicolumn_document(temp_path, output_path)
    else:
        if Converter is None:
            render_multicolumn_document(temp_path, output_path)
        else:
            try:
                cv = Converter(temp_path)
                cv.convert(output_path, start=0, end=None, multi_processing=False, parse_stream_table=False)
                cv.close()

                # Verify pdf2docx didn't drop content (e.g. empty lattice table)
                out_doc = docx.Document(output_path)
                out_chars = sum(len(p.text.strip()) for p in out_doc.paragraphs) + sum(
                    sum(len(c.text.strip()) for c in r.cells) for t in out_doc.tables for r in t.rows
                )
                if total_pdf_chars > 60 and out_chars < 0.25 * total_pdf_chars:
                    print("pdf2docx produced an empty or degraded docx, falling back to layout renderer...")
                    render_multicolumn_document(temp_path, output_path)
                else:
                    clean_docx_typography(output_path)
            except Exception as e:
                print(f"pdf2docx exception: {e}, using layout renderer...")
                render_multicolumn_document(temp_path, output_path)

    return {
        "output_path": output_path,
        "filename": output_filename,
        "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }


def _do_word_to_pdf(job_dir: str, temp_path: str, input_filename: str) -> dict:
    """Convert Word (.doc, .docx) to PDF using LibreOffice headless for instant, reliable conversion.
    Falls back to docx2pdf if LibreOffice is not available.
    """
    output_filename = input_filename.rsplit(".", 1)[0] + ".pdf"
    expected_output = os.path.join(job_dir, output_filename)

    # 1. Primary: Lightning-fast headless LibreOffice (1-2s, 100% layout fidelity, no COM/dialog hangs)
    try:
        pdf_path = convert_office_to_pdf(temp_path, job_dir, timeout=30)
        # Rename to clean target name if different
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
        print(f"LibreOffice conversion failed: {e}, falling back to docx2pdf...")

    # 2. Fallback: docx2pdf via COM
    try:
        import pythoncom
        pythoncom.CoInitialize()
        from docx2pdf import convert
        convert(temp_path, expected_output)
        return {
            "output_path": expected_output,
            "filename": output_filename,
            "media_type": "application/pdf",
        }
    finally:
        try:
            import pythoncom
            pythoncom.CoUninitialize()
        except Exception:
            pass


@router.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    temp_path = os.path.join(job_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    run_in_background(job_id, _do_pdf_to_word, job_dir, temp_path, file.filename)
    return JSONResponse(content={"job_id": job_id, "status": "processing"})


@router.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".doc", ".docx")):
        raise HTTPException(status_code=400, detail="File must be a Word document.")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    temp_path = os.path.join(job_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    run_in_background(job_id, _do_word_to_pdf, job_dir, temp_path, file.filename)
    return JSONResponse(content={"job_id": job_id, "status": "processing"})
