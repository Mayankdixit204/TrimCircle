from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from PIL import Image, ImageOps, UnidentifiedImageError

from .image_validation import validate_photo
from .job_store import cleanup_expired, create_job, delete_job, get_job, public_job, update_job
from .recommender import load_catalog
from .tryon import build_tryon_package

router = APIRouter(prefix="/v1/tryon/jobs", tags=["virtual try-on jobs"])

def _find_style(style_id: str) -> dict:
    style = next((item for item in load_catalog() if item["id"] == style_id), None)
    if not style:
        raise HTTPException(status_code=404, detail="Unknown hairstyle")
    return style

def _normalize_image(content: bytes, maximum: int = 1536) -> bytes:
    try:
        with Image.open(BytesIO(content)) as source:
            source = ImageOps.exif_transpose(source).convert("RGB")
            source.thumbnail((maximum, maximum), Image.Resampling.LANCZOS)
            output = BytesIO()
            source.save(output, "PNG", optimize=True)
            return output.getvalue()
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(status_code=422, detail="Unreadable image") from error

@router.post("", status_code=202)
async def submit_job(front: UploadFile = File(...), style_id: str = Form(...), color: str = Form("natural"), texture: str = Form("natural")) -> dict:
    cleanup_expired()
    content = await front.read(8 * 1024 * 1024 + 1)
    await front.close()
    check = validate_photo("front", content)
    if not check.valid:
        raise HTTPException(status_code=422, detail=check.messages)
    job = create_job(_find_style(style_id), color, texture, _normalize_image(content))
    return public_job(job)

@router.get("/{job_id}")
def job_status(job_id: str) -> dict:
    cleanup_expired()
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    return public_job(job)

@router.get("/{job_id}/package")
def job_package(job_id: str) -> StreamingResponse:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    archive, filename = build_tryon_package(Path(job["input_path"]).read_bytes(), "input.png", _find_style(job["style_id"]), job["color"], job["texture"])
    return StreamingResponse(archive, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=" + filename})

@router.post("/{job_id}/result")
async def upload_result(job_id: str, result: UploadFile = File(...)) -> dict:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    content = await result.read(12 * 1024 * 1024 + 1)
    await result.close()
    if len(content) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Result exceeds 12 MB")
    result_path = Path(job["input_path"]).parent / "result.png"
    result_path.write_bytes(_normalize_image(content))
    return public_job(update_job(job_id, status="completed", progress=100, result_path=str(result_path), error=None))

@router.get("/{job_id}/result")
def download_result(job_id: str) -> FileResponse:
    job = get_job(job_id)
    if not job or not job["result_path"] or not Path(job["result_path"]).exists():
        raise HTTPException(status_code=404, detail="Result is not ready")
    return FileResponse(job["result_path"], media_type="image/png", filename=f"trimcircle-{job_id}.png")

@router.delete("/{job_id}", status_code=204)
def remove_job(job_id: str) -> Response:
    if not delete_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return Response(status_code=204)
