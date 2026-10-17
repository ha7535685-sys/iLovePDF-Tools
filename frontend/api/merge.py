import os
import shutil
import uuid
import tempfile
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from .jobs import JOBS, run_in_background
import fitz  # PyMuPDF
from typing import List

router = APIRouter()
TEMP_DIR = os.path.join(tempfile.gettempdir(), "pdf_tools")
os.makedirs(TEMP_DIR, exist_ok=True)


def _do_merge(job_dir: str, file_paths: list[str], original_name: str) -> dict:
    merged_pdf = fitz.open()
    for path in file_paths:
        doc = fitz.open(path)
        merged_pdf.insert_pdf(doc)
        doc.close()
    output_filename = "merged.pdf"
    output_path = os.path.join(job_dir, output_filename)
    merged_pdf.save(output_path)
    merged_pdf.close()
    return {"output_path": output_path, "filename": output_filename, "media_type": "application/pdf"}


@router.post("/merge")
async def merge_pdfs(files: List[UploadFile] = File(...)):
    if not files or len(files) < 2:
        raise HTTPException(status_code=400, detail="Please upload at least two PDF files to merge.")

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF.")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    # Save files synchronously (fast — just writing to disk)
    file_paths = []
    for file in files:
        temp_path = os.path.join(job_dir, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_paths.append(temp_path)

    run_in_background(job_id, _do_merge, job_dir, file_paths, files[0].filename)
    return JSONResponse(content={"job_id": job_id, "status": "processing"})
