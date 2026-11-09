import unittest
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


class CaptureApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_rejects_unknown_view(self):
        response = self.client.post(
            "/v1/capture-check",
            files={"photo": ("frame.jpg", b"not-used", "image/jpeg")},
            data={"view": "diagonal"},
        )
        self.assertEqual(response.status_code, 422)

    def test_returns_actionable_guidance_when_no_face_is_visible(self):
        output = BytesIO()
        Image.new("RGB", (640, 480), "#777777").save(output, "JPEG")
        response = self.client.post(
            "/v1/capture-check",
            files={"photo": ("frame.jpg", output.getvalue(), "image/jpeg")},
            data={"view": "front"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertFalse(payload["ready"])
        self.assertEqual(payload["face_count"], 0)
        self.assertIn("face", payload["message"].lower())


if __name__ == "__main__":
    unittest.main()
