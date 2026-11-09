from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import mediapipe as mp
import numpy as np
from PIL import Image


MODEL_PATH = Path(__file__).parent / "models" / "face_landmarker.task"


@dataclass
class ViewAnalysis:
    view: str
    face_detected: bool
    pose: str
    pose_ok: bool
    message: str
    landmark_count: int = 0


def _distance(a, b) -> float:
    return float(((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5)


def _classify(landmarks) -> tuple[str, float, dict[str, float]]:
    face_length = _distance(landmarks[10], landmarks[152])
    cheek_width = _distance(landmarks[234], landmarks[454])
    forehead_width = _distance(landmarks[103], landmarks[332])
    jaw_width = _distance(landmarks[172], landmarks[397])
    length_ratio = face_length / max(cheek_width, 0.001)
    forehead_ratio = forehead_width / max(cheek_width, 0.001)
    jaw_ratio = jaw_width / max(cheek_width, 0.001)
    if length_ratio > 1.52:
        shape, confidence = "oblong", 0.72
    elif jaw_ratio > 0.90 and length_ratio < 1.46:
        shape, confidence = "square", 0.68
    elif forehead_ratio > 0.88 and jaw_ratio < 0.82:
        shape, confidence = "heart", 0.66
    elif forehead_ratio < 0.84 and jaw_ratio < 0.84:
        shape, confidence = "diamond", 0.64
    elif length_ratio < 1.30:
        shape, confidence = "round", 0.68
    else:
        shape, confidence = "oval", 0.62
    return shape, confidence, {
        "length_to_width": round(length_ratio, 2),
        "forehead_to_cheek": round(forehead_ratio, 2),
        "jaw_to_cheek": round(jaw_ratio, 2),
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
    front_landmarks = None
    with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
        for view in ("front", "left", "right"):
            with Image.open(BytesIO(images[view])) as source:
                source.thumbnail((768, 768))
                rgb = np.asarray(source.convert("RGB"))
            result = landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
            if not result.face_landmarks:
                views.append(ViewAnalysis(view, False, "unknown", False, "No clear face detected. Retake in even light."))
                continue
            landmarks = result.face_landmarks[0]
            xs = [point.x for point in landmarks]
            relative_nose = (landmarks[1].x - min(xs)) / max(max(xs) - min(xs), 0.001)
            pose = "left" if relative_nose < 0.43 else "right" if relative_nose > 0.57 else "front"
            pose_ok = pose == view or (view != "front" and pose != "front")
            views.append(ViewAnalysis(view, True, pose, pose_ok, "Face and landmarks detected.", len(landmarks)))
            if view == "front":
                front_landmarks = landmarks
    if front_landmarks is None:
        return {"face_shape": "unknown", "confidence": 0.0, "metrics": {}, "views": [item.__dict__ for item in views], "notice": "A front-facing face could not be measured."}
    shape, confidence, metrics = _classify(front_landmarks)
    return {"face_shape": shape, "confidence": confidence, "metrics": metrics, "views": [item.__dict__ for item in views], "notice": "Experimental geometry estimate. Confirm or change it before ranking styles."}
