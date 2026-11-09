import json
from functools import lru_cache
from pathlib import Path

from .models import Recommendation, RecommendationProfile


CATALOG_PATH = Path(__file__).parent / "data" / "hairstyles_extended.json"
LENGTH_ORDER = {"short": 0, "medium": 1, "long": 2}
MAINTENANCE_ORDER = {"low": 0, "medium": 1, "high": 2}


@lru_cache(maxsize=1)
def load_catalog() -> list[dict]:
    with CATALOG_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def recommend(profile: RecommendationProfile) -> list[Recommendation]:
    excluded = {item.strip().lower() for item in profile.excluded_styles if item.strip()}
    ranked: list[Recommendation] = []

    for style in load_catalog():
        if style["id"].lower() in excluded or style["name"].lower() in excluded:
            continue
        if LENGTH_ORDER[profile.current_length.value] < LENGTH_ORDER[style["minimum_length"]]:
            continue
        if profile.desired_length.value not in style["finished_lengths"]:
            continue

        score = 20
        reasons: list[str] = []

        if profile.face_shape.value == "unknown":
            score += 8
            reasons.append("Selected for broad face-shape versatility")
        elif profile.face_shape.value in style["face_shapes"]:
            score += 30
            reasons.append(f"Balances a {profile.face_shape.value} face shape")

        if profile.texture.value in style["textures"]:
            score += 25
            reasons.append(f"Works naturally with {profile.texture.value} hair")
        else:
            score -= 18

        if profile.density.value in style["densities"]:
            score += 15
            reasons.append(f"Suitable for {profile.density.value} hair density")
        else:
            score -= 10

        maintenance_gap = abs(
            MAINTENANCE_ORDER[profile.maintenance.value]
            - MAINTENANCE_ORDER[style["maintenance"]]
        )
        score += max(0, 10 - maintenance_gap * 7)
        if maintenance_gap == 0:
            reasons.append(f"Matches your {profile.maintenance.value}-maintenance preference")

        ranked.append(
            Recommendation(
                id=style["id"],
                name=style["name"],
                description=style["description"],
                score=max(0, min(100, score)),
                reasons=reasons[:3] or ["A flexible option worth discussing with a stylist"],
                maintenance=style["maintenance"],
                suitable_textures=style["textures"],
            )
        )

    return sorted(ranked, key=lambda item: (-item.score, item.name))[: profile.limit]

