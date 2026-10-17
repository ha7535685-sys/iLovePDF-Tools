import os
import time
import base64
from typing import Callable

# Global job store { job_id: {status, output_path, filename, media_type, error, start_time, elapsed_time, data_url} }
JOBS: dict = {}


def run_in_background(job_id: str, fn: Callable, *args, **kwargs):
    """Run `fn(*args, **kwargs)` immediately, updating JOBS[job_id].
    Supports both Vercel Serverless Functions and local FastAPI.
    """
    start_t = time.time()
    JOBS[job_id] = {
        "status": "processing",
        "start_time": start_t,
        "output_path": None,
        "filename": None,
        "media_type": None,
        "error": None,
        "elapsed_time": None,
        "data_url": None,
    }

    try:
        result = fn(*args, **kwargs)
        if isinstance(result, dict):
            JOBS[job_id].update(result)
        JOBS[job_id]["status"] = "completed"

        # Generate base64 Data URL for instant, zero-roundtrip downloads under 4.5MB
        out_p = JOBS[job_id].get("output_path")
        if out_p and os.path.exists(out_p):
            if os.path.getsize(out_p) < 4 * 1024 * 1024:
                media_t = JOBS[job_id].get("media_type", "application/pdf")
                with open(out_p, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                JOBS[job_id]["data_url"] = f"data:{media_t};base64,{b64}"
    except Exception as exc:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(exc)
    finally:
        JOBS[job_id]["elapsed_time"] = round(time.time() - start_t, 2)
