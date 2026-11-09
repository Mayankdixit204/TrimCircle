import unittest
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def test_image() -> bytes:
    output = BytesIO()
    Image.effect_noise((640, 640), 90).convert("RGB").save(output, "JPEG")
    return output.getvalue()


class JobApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.image = test_image()
        response = self.client.post(
            "/v1/tryon/jobs",
            files={"front": ("front.jpg", self.image, "image/jpeg")},
            data={"style_id": "textured-crop", "color": "dark-brown", "texture": "wavy"},
        )
        self.assertEqual(response.status_code, 202, response.text)
        self.job = response.json()

    def tearDown(self):
        self.client.delete(f"/v1/tryon/jobs/{self.job['id']}")

    def test_job_lifecycle(self):
        job_id = self.job["id"]
        self.assertEqual(self.job["status"], "awaiting_gpu")
        self.assertEqual(self.client.get(f"/v1/tryon/jobs/{job_id}").status_code, 200)
        package = self.client.get(f"/v1/tryon/jobs/{job_id}/package")
        self.assertEqual(package.status_code, 200)
        self.assertEqual(package.headers["content-type"], "application/zip")
        completed = self.client.post(
            f"/v1/tryon/jobs/{job_id}/result",
            files={"result": ("result.jpg", self.image, "image/jpeg")},
        )
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.json()["status"], "completed")
        result = self.client.get(f"/v1/tryon/jobs/{job_id}/result")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers["content-type"], "image/png")

    def test_delete_removes_private_job(self):
        job_id = self.job["id"]
        self.assertEqual(self.client.delete(f"/v1/tryon/jobs/{job_id}").status_code, 204)
        self.assertEqual(self.client.get(f"/v1/tryon/jobs/{job_id}").status_code, 404)


if __name__ == "__main__":
    unittest.main()
