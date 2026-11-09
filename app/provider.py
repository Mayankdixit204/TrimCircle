import os
from pathlib import Path
import httpx
from .job_store import get_job, update_job

class ProviderUnavailable(RuntimeError):
    pass

def process_remote_job(job_id: str) -> dict:
    endpoint = os.getenv("TRIMCIRCLE_GPU_ENDPOINT")
    if not endpoint:
        raise ProviderUnavailable("TRIMCIRCLE_GPU_ENDPOINT is not configured")
    job = get_job(job_id)
    if not job:
        raise LookupError("Job not found")
    update_job(job_id, status="generating", progress=45, error=None)
    headers = {}
    if os.getenv("TRIMCIRCLE_GPU_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["TRIMCIRCLE_GPU_TOKEN"]
    try:
        with Path(job["input_path"]).open("rb") as source:
            response = httpx.post(endpoint, files={"image": ("input.png", source, "image/png")}, data={"style_id": job["style_id"], "color": job["color"], "texture": job["texture"]}, headers=headers, timeout=300)
        response.raise_for_status()
        if not response.headers.get("content-type", "").startswith("image/"):
            raise RuntimeError("GPU provider did not return an image")
        result_path = Path(job["input_path"]).parent / "result.png"
        result_path.write_bytes(response.content)
        return update_job(job_id, status="completed", progress=100, result_path=str(result_path))
    except Exception as error:
        update_job(job_id, status="failed", progress=0, error=str(error)[:500])
        raise
