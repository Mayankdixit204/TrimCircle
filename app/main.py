from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .face_analysis import analyze_views
from .image_validation import validate_photo
from .job_api import router as job_router
from .overlay_api import router as overlay_router
from .models import PhotoCheck, RecommendationProfile, RecommendationResponse
from .recommender import load_catalog, recommend
from .tryon import build_tryon_package


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="TrimCircle Haircut Recommendation API",
    version="0.1.0",
    description="A lightweight, explainable rules-based recommendation MVP.",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(job_router)
app.include_router(overlay_router)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "studio.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "rules-baseline"}


@app.get("/v1/hairstyles")
def hairstyles() -> dict[str, list[dict]]:
    return {"items": load_catalog()}


@app.post("/v1/validate-photos", response_model=list[PhotoCheck])
async def validate_photos(
    front: UploadFile = File(...),
    left: UploadFile = File(...),
    right: UploadFile = File(...),
) -> list[PhotoCheck]:
    results: list[PhotoCheck] = []
    for view, upload in (("front", front), ("left", left), ("right", right)):
        content = await upload.read(8 * 1024 * 1024 + 1)
        results.append(validate_photo(view, content))
        await upload.close()
    return results


@app.post("/v1/analyze-face")
async def analyze_face(
    front: UploadFile = File(...),
    left: UploadFile = File(...),
    right: UploadFile = File(...),
) -> dict:
    images: dict[str, bytes] = {}
    for view, upload in (("front", front), ("left", left), ("right", right)):
        images[view] = await upload.read(8 * 1024 * 1024 + 1)
        await upload.close()
    checks = [validate_photo(view, content) for view, content in images.items()]
    if any(not check.valid for check in checks):
        return {
            "face_shape": "unknown", "confidence": 0.0, "metrics": {}, "views": [],
            "notice": "Fix photo-quality issues before facial analysis.",
            "photo_checks": [check.model_dump() for check in checks],
        }
    result = analyze_views(images)
    result["photo_checks"] = [check.model_dump() for check in checks]
    return result


@app.post("/v1/tryon/prepare")
async def prepare_tryon(
    front: UploadFile = File(...),
    style_id: str = Form(...),
    color: str = Form("natural"),
    texture: str = Form("natural"),
) -> StreamingResponse:
    content = await front.read(8 * 1024 * 1024 + 1)
    await front.close()
    check = validate_photo("front", content)
    if not check.valid:
        raise HTTPException(status_code=422, detail=check.messages)
    style = next((item for item in load_catalog() if item["id"] == style_id), None)
    if style is None:
        raise HTTPException(status_code=404, detail="Unknown hairstyle")
    archive, filename = build_tryon_package(content, front.filename or "front.jpg", style, color, texture)
    return StreamingResponse(
        archive,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=" + filename},
    )


@app.post("/v1/recommendations", response_model=RecommendationResponse)
def recommendations(profile: RecommendationProfile) -> RecommendationResponse:
    items = recommend(profile)
    notice = (
        "Face shape was not specified, so versatile styles were prioritized."
        if profile.face_shape.value == "unknown"
        else "Recommendations are an explainable baseline, not professional advice."
    )
    return RecommendationResponse(
        recommendations=items,
        face_shape_used=profile.face_shape,
        notice=notice,
    )

