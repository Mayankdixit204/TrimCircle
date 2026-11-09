from io import BytesIO

from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

from .models import PhotoCheck


MAX_BYTES = 8 * 1024 * 1024
MIN_SIDE = 320
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_photo(view: str, content: bytes) -> PhotoCheck:
    messages: list[str] = []
    if not content:
        return PhotoCheck(view=view, valid=False, messages=["Choose a photo for this view."])
    if len(content) > MAX_BYTES:
        return PhotoCheck(view=view, valid=False, messages=["Photo must be smaller than 8 MB."])

    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
        with Image.open(BytesIO(content)) as image:
            image_format = image.format
            image = ImageOps.exif_transpose(image)
            width, height = image.size
            if image_format not in ALLOWED_FORMATS:
                messages.append("Use a JPEG, PNG, or WebP photo.")
            if min(width, height) < MIN_SIDE:
                messages.append("Use a photo at least 320 pixels on each side.")

            thumbnail = image.convert("L")
            thumbnail.thumbnail((640, 640))
            edges = thumbnail.filter(ImageFilter.FIND_EDGES)
            sharpness = round(ImageStat.Stat(edges).var[0], 1)
            if sharpness < 35:
                messages.append("The photo may be blurry. Retake it in good light and hold still.")

            brightness = round(ImageStat.Stat(thumbnail).mean[0], 1)
            if brightness < 28:
                messages.append("The photo is too dark. Use even light on the face.")
            elif brightness > 235:
                messages.append("The photo is overexposed. Move away from harsh light.")

            return PhotoCheck(
                view=view,
                valid=not messages,
                width=width,
                height=height,
                sharpness=sharpness,
                messages=messages or ["Photo quality checks passed."],
            )
    except (UnidentifiedImageError, OSError):
        return PhotoCheck(view=view, valid=False, messages=["This file is not a readable image."])
