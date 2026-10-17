import os
import shutil
import uuid
import tempfile
import zipfile
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from .jobs import JOBS, run_in_background
import fitz  # PyMuPDF
from PIL import Image

router = APIRouter()
TEMP_DIR = os.path.join(tempfile.gettempdir(), "pdf_tools")
os.makedirs(TEMP_DIR, exist_ok=True)


def _do_pdf_to_jpg(job_dir: str, temp_path: str, original_filename: str) -> dict:
    doc = fitz.open(temp_path)
    if len(doc) == 1:
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=150)
        out_filename = original_filename.replace(".pdf", ".jpg")
        out_path = os.path.join(job_dir, out_filename)
        pix.save(out_path)
        return {"output_path": out_path, "filename": out_filename, "media_type": "image/jpeg"}
    else:
        zip_filename = original_filename.replace(".pdf", "_images.zip")
        zip_path = os.path.join(job_dir, zip_filename)
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=150)
                img_name = f"page_{page_num + 1}.jpg"
                img_path = os.path.join(job_dir, img_name)
                pix.save(img_path)
                zipf.write(img_path, img_name)
        return {"output_path": zip_path, "filename": zip_filename, "media_type": "application/zip"}


def _do_jpg_to_pdf(job_dir: str, image_paths: list[str]) -> dict:
    output_filename = "converted_images.pdf"
    output_path = os.path.join(job_dir, output_filename)
    img = Image.open(image_paths[0]).convert("RGB")
    other_images = [Image.open(p).convert("RGB") for p in image_paths[1:]]
    img.save(output_path, save_all=True, append_images=other_images)
    return {"output_path": output_path, "filename": output_filename, "media_type": "application/pdf"}


@router.post("/pdf-to-jpg")
async def pdf_to_jpg(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    temp_path = os.path.join(job_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    from .jobs import JOBS
    run_in_background(job_id, _do_pdf_to_jpg, job_dir, temp_path, file.filename)
    job_info = JOBS.get(job_id, {})
    return JSONResponse(content={
        "job_id": job_id,
        "status": job_info.get("status", "completed"),
        "filename": job_info.get("filename"),
        "elapsed_time": job_info.get("elapsed_time"),
        "download_url": job_info.get("data_url") or f"/api/tools/download/{job_id}",
    })


@router.post("/jpg-to-pdf")
async def jpg_to_pdf(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    for file in files:
        if not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
            raise HTTPException(status_code=400, detail="Files must be images (JPG/PNG).")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    image_paths = []
    for file in files:
        temp_path = os.path.join(job_dir, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        image_paths.append(temp_path)

    from .jobs import JOBS
    run_in_background(job_id, _do_jpg_to_pdf, job_dir, image_paths)
    job_info = JOBS.get(job_id, {})
    return JSONResponse(content={
        "job_id": job_id,
        "status": job_info.get("status", "completed"),
        "filename": job_info.get("filename"),
        "elapsed_time": job_info.get("elapsed_time"),
        "download_url": job_info.get("data_url") or f"/api/tools/download/{job_id}",
    })
