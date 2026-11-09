import unittest
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


class OverlayApiTests(unittest.TestCase):
    def test_returns_three_editable_anchors(self):
        output = BytesIO()
        Image.effect_noise((480, 640), 70).convert("RGB").save(output, "JPEG")
        image = output.getvalue()
        response = TestClient(app).post(
            "/v1/overlay/anchors",
            files={view: (f"{view}.jpg", image, "image/jpeg") for view in ("front", "left", "right")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertTrue(payload["editable"])
        self.assertEqual([item["view"] for item in payload["anchors"]], ["front", "left", "right"])
        self.assertTrue(all(0 <= item["center_x"] <= 1 for item in payload["anchors"]))


if __name__ == "__main__":
    unittest.main()
