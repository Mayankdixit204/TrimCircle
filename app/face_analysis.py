from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import mediapipe as mp
import numpy as np
from PIL import Image, ImageOps

from .geometry import front_measurements, profile_measurements


MODEL_PATH = Path(__file__).parent / "models" / "face_landmarker.task"


@dataclass
class ViewAnalysis:
    view: str
    face_detected: bool
    pose: str
    pose_ok: bool
    message: str
    landmark_count: int = 0


def _classify(metrics: dict[str, float]) -> tuple[str, str | None, str]:
    length_ratio = metrics["length_to_cheek_span"]
    forehead_ratio = metrics["forehead_to_cheek_span"]
    jaw_ratio = metrics["jaw_to_cheek_span"]
    if length_ratio > 1.52:
        shape, alternative = "oblong", "oval"
    elif jaw_ratio > 0.90 and length_ratio < 1.46:
        shape, alternative = "square", "round"
    elif forehead_ratio > 0.88 and jaw_ratio < 0.82:
        shape, alternative = "heart", "diamond"
    elif forehead_ratio < 0.84 and jaw_ratio < 0.84:
        shape, alternative = "diamond", "oval"
    elif length_ratio < 1.30:
        shape, alternative = "round", "square"
    else:
        shape, alternative = "oval", "oblong"
    # Thresholds are an unvalidated baseline, so no probability is returned.
    return shape, alternative, "unvalidated"


def check_capture(content: bytes, expected_view: str) -> dict:
    """Return actionable live-capture guidance for one camera frame."""
    if expected_view not in {"front", "left", "right"}:
        raise ValueError("Unsupported capture view")

    with Image.open(BytesIO(content)) as source:
        source = ImageOps.exif_transpose(source).convert("RGB")
        source.thumbnail((640, 640), Image.Resampling.LANCZOS)
        rgb = np.asarray(source)

    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_faces=2,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
    )
    with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
        result = landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

    face_count = len(result.face_landmarks)
    base = {
        "face_count": face_count,
        "centered": False,
        "face_size_ok": False,
        "pose": "unknown",
        "pose_ok": False,
        "ready": False,
        "center": None,
        "face_span": None,
    }
    if face_count == 0:
        return {**base, "message": "No face found. Move into the oval and face the camera."}
    if face_count > 1:
        return {**base, "message": "Only one person should be visible."}

    landmarks = result.face_landmarks[0]
    xs = [point.x for point in landmarks]
    ys = [point.y for point in landmarks]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    face_span = max(max_x - min_x, max_y - min_y)
    centered = abs(center_x - 0.5) <= 0.11 and abs(center_y - 0.5) <= 0.13
    face_size_ok = 0.32 <= face_span <= 0.78
    relative_nose = (landmarks[1].x - min_x) / max(max_x - min_x, 0.001)
    pose = "left" if relative_nose < 0.43 else "right" if relative_nose > 0.57 else "front"
    pose_ok = pose == expected_view
    ready = centered and face_size_ok and pose_ok

    if not centered:
        message = "Move your face to the center of the oval."
    elif face_span < 0.32:
        message = "Move closer to the camera."
    elif face_span > 0.78:
        message = "Move slightly farther from the camera."
    elif not pose_ok and expected_view == "front":
        message = "Look straight at the camera."
    elif not pose_ok:
        message = f"Turn your head toward your {expected_view} until your profile is visible."
    else:
        message = "Position looks good. Hold still and capture."

    return {
        **base,
        "centered": centered,
        "face_size_ok": face_size_ok,
        "pose": pose,
        "pose_ok": pose_ok,
        "ready": ready,
        "center": {"x": round(center_x, 4), "y": round(center_y, 4)},
        "face_span": round(face_span, 4),
        "message": message,
    }


def analyze_views(images: dict[str, bytes]) -> dict:
    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_faces=1,
        min_face_detection_confidence=0.45,
        min_face_presence_confidence=0.45,
    )
    views: list[ViewAnalysis] = []
    view_landmarks: dict[str, tuple[list, int, int]] = {}
    with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
        for view in ("front", "left", "right"):
            with Image.open(BytesIO(images[view])) as source:
                source = ImageOps.exif_transpose(source).convert("RGB")
                original_width, original_height = source.size
                source.thumbnail((768, 768))
                rgb = np.asarray(source)
            result = landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
            if not result.face_landmarks:
                views.append(ViewAnalysis(view, False, "unknown", False, "No clear face detected. Retake in even light."))
                continue
            landmarks = result.face_landmarks[0]
            xs = [point.x for point in landmarks]
            relative_nose = (landmarks[1].x - min(xs)) / max(max(xs) - min(xs), 0.001)
            pose = "left" if relative_nose < 0.43 else "right" if relative_nose > 0.57 else "front"
            pose_ok = pose == view
            views.append(ViewAnalysis(view, True, pose, pose_ok, "Face and landmarks detected.", len(landmarks)))
            view_landmarks[view] = (landmarks, original_width, original_height)
    if "front" not in view_landmarks:
        return {"face_shape": "unknown", "alternative_face_shape": None, "uncertainty": "unusable", "metrics": {}, "measurements": [], "views": [item.__dict__ for item in views], "notice": "A front-facing face could not be measured."}

    front, width, height = view_landmarks["front"]
    measurements = front_measurements(front, width, height)
    for view in ("left", "right"):
        if view in view_landmarks:
            points, view_width, view_height = view_landmarks[view]
            measurements.extend(profile_measurements(points, view_width, view_height, view))
    metric_values = {item.name: item.value for item in measurements if item.valid and item.value is not None}
    shape, alternative, uncertainty = _classify(metric_values)
    legacy_metrics = {
        "length_to_width": round(metric_values["length_to_cheek_span"], 2),
        "forehead_to_cheek": round(metric_values["forehead_to_cheek_span"], 2),
        "jaw_to_cheek": round(metric_values["jaw_to_cheek_span"], 2),
    }
    valid_views = sum(1 for item in views if item.face_detected and item.pose_ok)
    if valid_views < 3:
        uncertainty = "high"
    return {
        "face_shape": shape,
        "alternative_face_shape": alternative,
        "uncertainty": uncertainty,
        "metrics": legacy_metrics,
        "measurements": [item.to_dict() for item in measurements],
        "views": [item.__dict__ for item in views],
        "notice": "Unvalidated geometry-based styling estimate. Confirm or change it before ranking styles.",
    }
