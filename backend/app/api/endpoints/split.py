import os
import shutil
import uuid
import tempfile
import zipfile
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from .jobs import JOBS, run_in_background
import fitz  # PyMuPDF

router = APIRouter()
TEMP_DIR = os.path.join(tempfile.gettempdir(), "pdf_tools")
os.makedirs(TEMP_DIR, exist_ok=True)


def _do_split(job_dir: str, temp_path: str, original_filename: str, ranges: str) -> dict:
    doc = fitz.open(temp_path)
    total_pages = len(doc)

    parsed_ranges = []
    for r in ranges.split(","):
        r = r.strip()
        if "-" in r:
            start, end = r.split("-")
            parsed_ranges.append((int(start) - 1, int(end) - 1))
        else:
            parsed_ranges.append((int(r) - 1, int(r) - 1))

    output_files = []
    for idx, (start, end) in enumerate(parsed_ranges):
        start = max(0, min(start, total_pages - 1))
        end = max(0, min(end, total_pages - 1))
        if start > end:
            start, end = end, start
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start, to_page=end)
        out_name = f"split_{idx + 1}.pdf"
        out_path = os.path.join(job_dir, out_name)
        new_doc.save(out_path)
        new_doc.close()
        output_files.append(out_path)

    doc.close()

    if len(output_files) == 1:
        return {
            "output_path": output_files[0],
            "filename": f"split_{original_filename}",
            "media_type": "application/pdf",
        }
    else:
        zip_path = os.path.join(job_dir, "split_files.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for f in output_files:
                zipf.write(f, os.path.basename(f))
        return {"output_path": zip_path, "filename": "split_files.zip", "media_type": "application/zip"}


@router.post("/split")
async def split_pdf(
    file: UploadFile = File(...),
    split_mode: str = Form(default="fixed_ranges"),
    ranges: str = Form(default="1-1"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    temp_path = os.path.join(job_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    run_in_background(job_id, _do_split, job_dir, temp_path, file.filename, ranges)
    return JSONResponse(content={"job_id": job_id, "status": "processing"})
