import unittest
from io import BytesIO

from PIL import Image

from app.image_validation import validate_photo


class ImageValidationTests(unittest.TestCase):
    def test_rejects_non_image(self):
        result = validate_photo("front", b"not an image")
        self.assertFalse(result.valid)

    def test_reads_valid_image_dimensions(self):
        buffer = BytesIO()
        image = Image.effect_noise((480, 480), 80).convert("RGB")
        image.save(buffer, format="JPEG")
        result = validate_photo("front", buffer.getvalue())
        self.assertEqual(result.width, 480)
        self.assertEqual(result.height, 480)
        self.assertIsNotNone(result.sharpness)


if __name__ == "__main__":
    unittest.main()

