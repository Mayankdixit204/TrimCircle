"""Aspect-ratio-correct facial geometry primitives.

MediaPipe coordinates are normalized independently on each axis.  Distances must
therefore be converted back to one pixel coordinate system before ratios are
computed.  The measurements in this module are landmark-derived styling
proxies, not anatomical measurements.
"""

from dataclasses import asdict, dataclass
from math import hypot
from typing import Sequence


@dataclass(frozen=True)
class Measurement:
    name: str
    value: float | None
    unit: str
    source_view: str
    quality: str
    valid: bool
    limitation: str

    def to_dict(self) -> dict:
        return asdict(self)


def pixel_point(point, width: int, height: int) -> tuple[float, float]:
    """Convert a normalized landmark to original-image pixel coordinates."""
    return float(point.x) * width, float(point.y) * height


def pixel_distance(a, b, width: int, height: int) -> float:
    ax, ay = pixel_point(a, width, height)
    bx, by = pixel_point(b, width, height)
    return hypot(bx - ax, by - ay)


def _ratio(name: str, numerator: float, denominator: float, view: str) -> Measurement:
    if denominator <= 1e-6:
        return Measurement(name, None, "ratio", view, "unusable", False, "Reference span is zero or unavailable.")
    return Measurement(
        name,
        round(numerator / denominator, 4),
        "ratio",
        view,
        "usable",
        True,
        "Landmark-derived styling proxy; not an anatomical boundary measurement.",
    )


def front_measurements(landmarks: Sequence, width: int, height: int) -> list[Measurement]:
    face_height = pixel_distance(landmarks[10], landmarks[152], width, height)
    cheek_span = pixel_distance(landmarks[234], landmarks[454], width, height)
    forehead_span = pixel_distance(landmarks[103], landmarks[332], width, height)
    jaw_span = pixel_distance(landmarks[172], landmarks[397], width, height)
    chin_span = pixel_distance(landmarks[148], landmarks[377], width, height)
    return [
        _ratio("length_to_cheek_span", face_height, cheek_span, "front"),
        _ratio("forehead_to_cheek_span", forehead_span, cheek_span, "front"),
        _ratio("jaw_to_cheek_span", jaw_span, cheek_span, "front"),
        _ratio("chin_to_jaw_span", chin_span, jaw_span, "front"),
    ]


def profile_measurements(landmarks: Sequence, width: int, height: int, view: str) -> list[Measurement]:
    face_height = pixel_distance(landmarks[10], landmarks[152], width, height)
    chin_projection = pixel_distance(landmarks[1], landmarks[152], width, height)
    return [_ratio("nose_to_chin_to_face_height", chin_projection, face_height, view)]
