import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from .endpoints.jobs import JOBS
from .endpoints import merge, split, compress, convert, images, security, modify, excel

api_router = APIRouter()

# ── Shared job status & download endpoints ────────────────────────────────────

@api_router.get("/tools/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Poll this endpoint to check conversion status."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] == "completed":
        return JSONResponse(content={
            "status": "completed",
            "filename": job.get("filename"),
            "elapsed_time": job.get("elapsed_time"),
            "download_url": job.get("data_url") or f"/api/tools/download/{job_id}",
        })
    elif job["status"] == "failed":
        return JSONResponse(content={
            "status": "failed",
            "error": job.get("error"),
            "elapsed_time": job.get("elapsed_time")
        })
    return JSONResponse(content={
        "status": job["status"],
        "elapsed_time": job.get("elapsed_time"),
        "download_url": job.get("data_url") or f"/api/tools/download/{job_id}",
    })


@api_router.get("/tools/download/{job_id}")
async def download_result(job_id: str):
    """Download the processed file once status is 'completed'."""
    job = JOBS.get(job_id)
    if not job or job["status"] != "completed" or not job.get("output_path"):
        raise HTTPException(status_code=404, detail="File not ready or job not found")
    if not os.path.exists(job["output_path"]):
        raise HTTPException(status_code=404, detail="Output file missing from disk")
    return FileResponse(
        path=job["output_path"],
        filename=job["filename"],
        media_type=job.get("media_type", "application/octet-stream"),
    )


# ── Tool routers ──────────────────────────────────────────────────────────────

api_router.include_router(merge.router, prefix="/tools", tags=["tools"])
api_router.include_router(split.router, prefix="/tools", tags=["tools"])
api_router.include_router(compress.router, prefix="/tools", tags=["tools"])
api_router.include_router(convert.router, prefix="/tools", tags=["tools"])
api_router.include_router(images.router, prefix="/tools", tags=["tools"])
api_router.include_router(security.router, prefix="/tools", tags=["tools"])
api_router.include_router(modify.router, prefix="/tools", tags=["tools"])
api_router.include_router(excel.router, prefix="/tools", tags=["tools"])
