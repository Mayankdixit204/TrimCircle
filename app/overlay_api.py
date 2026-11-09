from io import BytesIO

import mediapipe as mp
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from .face_analysis import MODEL_PATH


router = APIRouter(prefix="/v1/overlay", tags=["2D hairstyle overlay"])


def _anchor(content: bytes, view: str, landmarker) -> dict:
    try:
        with Image.open(BytesIO(content)) as source:
            source = ImageOps.exif_transpose(source).convert("RGB")
            width, height = source.size
            source.thumbnail((768, 768), Image.Resampling.LANCZOS)
            pixels = np.asarray(source)
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(status_code=422, detail=f"Unreadable {view} image") from error

    result = landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=pixels))
    if not result.face_landmarks:
        return {
            "view": view, "detected": False, "center_x": 0.5, "hairline_y": 0.23,
            "face_width": 0.45, "rotation": 0.0, "image_width": width, "image_height": height,
        }
    points = result.face_landmarks[0]
    xs = [point.x for point in points]
    left_eye, right_eye = points[33], points[263]
    angle = float(np.degrees(np.arctan2(right_eye.y - left_eye.y, right_eye.x - left_eye.x)))
    return {
        "view": view,
        "detected": True,
        "center_x": round((min(xs) + max(xs)) / 2, 4),
        "hairline_y": round(points[10].y, 4),
        "face_width": round(max(xs) - min(xs), 4),
        "rotation": round(angle, 2),
        "image_width": width,
        "image_height": height,
    }


@router.post("/anchors")
async def overlay_anchors(
    front: UploadFile = File(...),
    left: UploadFile = File(...),
    right: UploadFile = File(...),
) -> dict:
    uploads = {"front": front, "left": left, "right": right}
    images = {}
    for view, upload in uploads.items():
        images[view] = await upload.read(8 * 1024 * 1024 + 1)
        await upload.close()
        if len(images[view]) > 8 * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"{view} image exceeds 8 MB")

    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_faces=1,
        min_face_detection_confidence=0.4,
        min_face_presence_confidence=0.4,
    )
    with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
        anchors = [_anchor(images[view], view, landmarker) for view in ("front", "left", "right")]
    return {"anchors": anchors, "method": "mediapipe-face-landmarks", "editable": True}
