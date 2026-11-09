from enum import Enum

from pydantic import BaseModel, Field


class FaceShape(str, Enum):
    unknown = "unknown"
    oval = "oval"
    round = "round"
    square = "square"
    oblong = "oblong"
    heart = "heart"
    diamond = "diamond"


class HairTexture(str, Enum):
    straight = "straight"
    wavy = "wavy"
    curly = "curly"
    coily = "coily"


class HairDensity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class HairLength(str, Enum):
    short = "short"
    medium = "medium"
    long = "long"


class Maintenance(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RecommendationProfile(BaseModel):
    face_shape: FaceShape = FaceShape.unknown
    texture: HairTexture
    density: HairDensity
    current_length: HairLength
    desired_length: HairLength
    maintenance: Maintenance
    excluded_styles: list[str] = Field(default_factory=list, max_length=20)
    limit: int = Field(default=5, ge=1, le=10)


class Recommendation(BaseModel):
    id: str
    name: str
    description: str
    score: int
    reasons: list[str]
    maintenance: Maintenance
    suitable_textures: list[HairTexture]


class RecommendationResponse(BaseModel):
    recommendations: list[Recommendation]
    face_shape_used: FaceShape
    notice: str


class PhotoCheck(BaseModel):
    view: str
    valid: bool
    width: int | None = None
    height: int | None = None
    sharpness: float | None = None
    messages: list[str]

