import json
import re
import zipfile
from datetime import datetime, timezone
from io import BytesIO

from PIL import Image, ImageOps


ALLOWED_COLORS = {
    "natural": "preserve the person's natural hair color",
    "black": "natural soft black hair",
    "dark-brown": "natural dark brown hair",
    "warm-brown": "warm medium brown hair",
    "blonde": "natural dimensional blonde hair",
    "copper": "natural dimensional copper hair",
}


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")[:60]


def build_tryon_package(
    image_bytes: bytes,
    filename: str,
    style: dict,
    color: str,
    texture: str,
) -> tuple[BytesIO, str]:
    selected_color = ALLOWED_COLORS.get(color, ALLOWED_COLORS["natural"])
    with Image.open(BytesIO(image_bytes)) as source:
        source = ImageOps.exif_transpose(source).convert("RGB")
        source.thumbnail((1536, 1536), Image.Resampling.LANCZOS)
        normalized = BytesIO()
        source.save(normalized, format="PNG", optimize=True)

    job_id = datetime.now(timezone.utc).strftime("tryon-%Y%m%d-%H%M%S")
    prompt = (
        f"Photorealistic hairstyle try-on. Change only the hair to a {style['name']}. "
        f"Style description: {style['description']} Hair texture: {texture}. "
        f"Hair color: {selected_color}. Preserve the exact facial identity, facial features, "
        "skin tone, expression, head position, ears, neck, clothing, lighting, camera angle, "
        "and background. Realistic hair strands, hairline, volume, shadows, and edge blending."
    )
    negative_prompt = (
        "changed identity, changed face, altered eyes, altered nose, altered lips, different person, "
        "beautified face, deformed face, extra face, wig-like edges, plastic hair, blurry hair, "
        "changed clothes, changed background, text, watermark"
    )
    manifest = {
        "schema_version": "1.0",
        "job_id": job_id,
        "source_file": "input.png",
        "expected_output_file": "result.png",
        "style": {"id": style["id"], "name": style["name"], "description": style["description"]},
        "controls": {"color": color, "texture": texture, "identity_strength": 0.9, "guidance_scale": 7.0, "steps": 30},
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "privacy": {"contains_biometric_image": True, "publish_allowed": False, "delete_after_generation": True},
    }
    readme = (
        "TrimCircle virtual try-on job\n\n"
        "1. Upload this ZIP to the private Kaggle workflow.\n"
        "2. Generate only the hair region using job.json.\n"
        "3. Save the final image as result.png.\n"
        "4. Import result.png into TrimCircle.\n"
        "5. Delete the Kaggle input and output after download.\n"
    )

    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        package.writestr("input.png", normalized.getvalue())
        package.writestr("job.json", json.dumps(manifest, indent=2))
        package.writestr("prompt.txt", prompt + "\n\nNEGATIVE PROMPT:\n" + negative_prompt)
        package.writestr("README.txt", readme)
    archive.seek(0)
    return archive, f"{job_id}-{_safe_name(style['name'])}.zip"
