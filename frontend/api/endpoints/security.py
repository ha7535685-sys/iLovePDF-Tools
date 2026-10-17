import os
import shutil
import uuid
import tempfile
import fitz  # PyMuPDF (fast C engine)
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from .jobs import run_in_background

router = APIRouter()
TEMP_DIR = os.path.join(tempfile.gettempdir(), "pdf_tools")
os.makedirs(TEMP_DIR, exist_ok=True)


def _do_protect(job_dir: str, temp_path: str, original_filename: str, password: str) -> dict:
    """Protect PDF using native C PyMuPDF AES-256 encryption (instantaneous)."""
    doc = fitz.open(temp_path)
    output_filename = original_filename.rsplit(".", 1)[0] + "_protected.pdf"
    output_path = os.path.join(job_dir, output_filename)

    # Encrypt with modern AES-256
    doc.save(
        output_path,
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw=password,
        owner_pw=password,
    )
    doc.close()
    return {"output_path": output_path, "filename": output_filename, "media_type": "application/pdf"}


def _do_unlock(job_dir: str, temp_path: str, original_filename: str, password: str) -> dict:
    """Unlock PDF using native C PyMuPDF decryption (instantaneous)."""
    doc = fitz.open(temp_path)
    if doc.is_encrypted:
        auth_status = doc.authenticate(password)
        if auth_status == 0:
            doc.close()
            raise ValueError("Incorrect password.")

    output_filename = original_filename.rsplit(".", 1)[0] + "_unlocked.pdf"
    output_path = os.path.join(job_dir, output_filename)

    doc.save(output_path, encryption=fitz.PDF_ENCRYPT_NONE)
    doc.close()
    return {"output_path": output_path, "filename": output_filename, "media_type": "application/pdf"}


@router.post("/protect-pdf")
async def protect_pdf(
    file: UploadFile = File(...),
    password: str = Form(...),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    temp_path = os.path.join(job_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    from .jobs import JOBS
    run_in_background(job_id, _do_protect, job_dir, temp_path, file.filename, password)
    job_info = JOBS.get(job_id, {})
    return JSONResponse(content={
        "job_id": job_id,
        "status": job_info.get("status", "completed"),
        "filename": job_info.get("filename"),
        "elapsed_time": job_info.get("elapsed_time"),
        "download_url": job_info.get("data_url") or f"/api/tools/download/{job_id}",
    })


@router.post("/unlock-pdf")
async def unlock_pdf(
    file: UploadFile = File(...),
    password: str = Form(...),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    temp_path = os.path.join(job_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    from .jobs import JOBS
    run_in_background(job_id, _do_unlock, job_dir, temp_path, file.filename, password)
    job_info = JOBS.get(job_id, {})
    return JSONResponse(content={
        "job_id": job_id,
        "status": job_info.get("status", "completed"),
        "filename": job_info.get("filename"),
        "elapsed_time": job_info.get("elapsed_time"),
        "download_url": job_info.get("data_url") or f"/api/tools/download/{job_id}",
    })
