import json
import unittest
import zipfile
from io import BytesIO

from PIL import Image

from app.tryon import build_tryon_package


class TryOnPackageTests(unittest.TestCase):
    def test_package_contains_normalized_input_and_manifest(self):
        source = BytesIO()
        Image.new("RGB", (1800, 1200), "#8f6b55").save(source, "JPEG")
        style = {"id": "textured-crop", "name": "Textured Crop", "description": "Short textured layers."}
        package, filename = build_tryon_package(source.getvalue(), "face.jpg", style, "dark-brown", "wavy")
        self.assertTrue(filename.endswith("textured-crop.zip"))
        with zipfile.ZipFile(package) as archive:
            self.assertEqual(set(archive.namelist()), {"input.png", "job.json", "prompt.txt", "README.txt"})
            manifest = json.loads(archive.read("job.json"))
            self.assertEqual(manifest["style"]["id"], "textured-crop")
            self.assertTrue(manifest["privacy"]["contains_biometric_image"])


if __name__ == "__main__":
    unittest.main()
