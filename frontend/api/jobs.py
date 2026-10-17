"""
Shared async job management.
All endpoints save work here and return {job_id} immediately.
Frontend polls GET /api/tools/jobs/{job_id} until status=="completed".
"""
import time
from typing import Callable
from concurrent.futures import ThreadPoolExecutor

# Global job store { job_id: {status, output_path, filename, media_type, error, start_time, elapsed_time} }
JOBS: dict = {}

# Sized for responsive multi-user handling
executor = ThreadPoolExecutor(max_workers=16)


def run_in_background(job_id: str, fn: Callable, *args, **kwargs):
    """Run `fn(*args, **kwargs)` in a thread pool, updating JOBS[job_id]."""
    JOBS[job_id] = {
        "status": "processing",
        "start_time": time.time(),
        "output_path": None,
        "filename": None,
        "media_type": None,
        "error": None,
        "elapsed_time": None,
    }

    def _worker():
        try:
            result = fn(*args, **kwargs)
            if isinstance(result, dict):
                JOBS[job_id].update(result)
            JOBS[job_id]["status"] = "completed"
        except Exception as exc:
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["error"] = str(exc)
        finally:
            start_t = JOBS[job_id].get("start_time", time.time())
            JOBS[job_id]["elapsed_time"] = round(time.time() - start_t, 2)

    executor.submit(_worker)
