import os
import shutil
import uuid
import tempfile
import fitz
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from .jobs import run_in_background

router = APIRouter()
TEMP_DIR = os.path.join(tempfile.gettempdir(), "pdf_tools")
os.makedirs(TEMP_DIR, exist_ok=True)

def _do_add_page_numbers(job_dir: str, temp_path: str, original_filename: str, position: str) -> dict:
    doc = fitz.open(temp_path)
    for i, page in enumerate(doc):
        text = str(i + 1)
        rect = page.rect
        # default bottom-right
        x, y = rect.width - 50, rect.height - 50
        if position == "bottom-center":
            x, y = rect.width / 2, rect.height - 50
        elif position == "bottom-left":
            x, y = 50, rect.height - 50
        elif position == "top-right":
            x, y = rect.width - 50, 50
        elif position == "top-center":
            x, y = rect.width / 2, 50
        elif position == "top-left":
            x, y = 50, 50
            
        p = fitz.Point(x, y)
        page.insert_text(p, text, fontsize=12, color=(0, 0, 0))

    output_filename = original_filename.replace(".pdf", "_numbered.pdf")
    output_path = os.path.join(job_dir, output_filename)
    doc.save(output_path)
    doc.close()
    return {"output_path": output_path, "filename": output_filename, "media_type": "application/pdf"}

def _do_rotate(job_dir: str, temp_path: str, original_filename: str, rotation: int) -> dict:
    doc = fitz.open(temp_path)
    for page in doc:
        page.set_rotation((page.rotation + rotation) % 360)
    output_filename = original_filename.replace(".pdf", "_rotated.pdf")
    output_path = os.path.join(job_dir, output_filename)
    doc.save(output_path)
    doc.close()
    return {"output_path": output_path, "filename": output_filename, "media_type": "application/pdf"}

def _do_watermark(job_dir: str, temp_path: str, original_filename: str, text: str) -> dict:
    doc = fitz.open(temp_path)
    for page in doc:
        rect = page.rect
        p = fitz.Point(rect.width / 2 - 100, rect.height / 2 + 100)
        page.insert_text(p, text, fontsize=40, color=(0.5, 0.5, 0.5), fill_opacity=0.3, morph=(p, fitz.Matrix(45)))
    output_filename = original_filename.replace(".pdf", "_watermarked.pdf")
    output_path = os.path.join(job_dir, output_filename)
    doc.save(output_path)
    doc.close()
    return {"output_path": output_path, "filename": output_filename, "media_type": "application/pdf"}

def _do_remove_pages(job_dir: str, temp_path: str, original_filename: str, pages: str) -> dict:
    doc = fitz.open(temp_path)
    pages_to_remove = [int(p.strip()) - 1 for p in pages.split(",") if p.strip().isdigit()]
    pages_to_keep = [i for i in range(len(doc)) if i not in pages_to_remove]
    doc.select(pages_to_keep)
    output_filename = original_filename.replace(".pdf", "_removed.pdf")
    output_path = os.path.join(job_dir, output_filename)
    doc.save(output_path)
    doc.close()
    return {"output_path": output_path, "filename": output_filename, "media_type": "application/pdf"}

def _do_extract_pages(job_dir: str, temp_path: str, original_filename: str, pages: str) -> dict:
    doc = fitz.open(temp_path)
    pages_to_extract = [int(p.strip()) - 1 for p in pages.split(",") if p.strip().isdigit()]
    doc.select([i for i in pages_to_extract if 0 <= i < len(doc)])
    output_filename = original_filename.replace(".pdf", "_extracted.pdf")
    output_path = os.path.join(job_dir, output_filename)
    doc.save(output_path)
    doc.close()
    return {"output_path": output_path, "filename": output_filename, "media_type": "application/pdf"}

def _do_organize(job_dir: str, temp_path: str, original_filename: str, order: str) -> dict:
    doc = fitz.open(temp_path)
    new_order = [int(p.strip()) - 1 for p in order.split(",") if p.strip().isdigit()]
    doc.select([i for i in new_order if 0 <= i < len(doc)])
    output_filename = original_filename.replace(".pdf", "_organized.pdf")
    output_path = os.path.join(job_dir, output_filename)
    doc.save(output_path)
    doc.close()
    return {"output_path": output_path, "filename": output_filename, "media_type": "application/pdf"}

# ── Route helpers ──────────────────────────────────────────────────────────────

async def _save_and_run(file: UploadFile, fn, *extra_args):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    temp_path = os.path.join(job_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    from .jobs import JOBS
    run_in_background(job_id, fn, job_dir, temp_path, file.filename, *extra_args)
    job_info = JOBS.get(job_id, {})
    return JSONResponse(content={
        "job_id": job_id,
        "status": job_info.get("status", "completed"),
        "filename": job_info.get("filename"),
        "elapsed_time": job_info.get("elapsed_time"),
        "download_url": job_info.get("data_url") or f"/api/tools/download/{job_id}",
    })

@router.post("/add-page-numbers")
async def add_page_numbers(file: UploadFile = File(...), position: str = Form("bottom-right")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    return await _save_and_run(file, _do_add_page_numbers, position)

@router.post("/rotate-pdf")
async def rotate_pdf(file: UploadFile = File(...), rotation: int = Form(90)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    return await _save_and_run(file, _do_rotate, rotation)

@router.post("/watermark-pdf")
async def watermark_pdf(file: UploadFile = File(...), text: str = Form("Watermark")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    return await _save_and_run(file, _do_watermark, text)

@router.post("/remove-pages")
async def remove_pages(file: UploadFile = File(...), pages: str = Form("")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    return await _save_and_run(file, _do_remove_pages, pages)

@router.post("/extract-pages")
async def extract_pages(file: UploadFile = File(...), pages: str = Form("")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    return await _save_and_run(file, _do_extract_pages, pages)

@router.post("/organize-pdf")
async def organize_pdf(file: UploadFile = File(...), order: str = Form("")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    return await _save_and_run(file, _do_organize, order)
