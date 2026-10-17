import os
import shutil
import uuid
import tempfile
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from .jobs import JOBS, run_in_background
import fitz  # PyMuPDF

router = APIRouter()
TEMP_DIR = os.path.join(tempfile.gettempdir(), "pdf_tools")
os.makedirs(TEMP_DIR, exist_ok=True)


def _do_compress(job_dir: str, temp_path: str, original_filename: str, level: str) -> dict:
    doc = fitz.open(temp_path)
    output_filename = f"compressed_{original_filename}"
    output_path = os.path.join(job_dir, output_filename)
    if level == "extreme":
        doc.save(output_path, garbage=4, deflate=True, deflate_images=True)
    elif level == "low":
        doc.save(output_path, garbage=1, deflate=True)
    else:
        # Recommended: 100% lossless, preserves all fonts, text, vectors and images exactly
        doc.save(output_path, garbage=3, deflate=True)
    doc.close()
    return {"output_path": output_path, "filename": output_filename, "media_type": "application/pdf"}


@router.post("/compress")
async def compress_pdf(
    file: UploadFile = File(...),
    level: str = Form(default="recommended"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    temp_path = os.path.join(job_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    run_in_background(job_id, _do_compress, job_dir, temp_path, file.filename, level)
    return JSONResponse(content={"job_id": job_id, "status": "processing"})
