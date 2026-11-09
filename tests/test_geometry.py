import unittest

from app.geometry import pixel_distance, pixel_point


class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class GeometryTests(unittest.TestCase):
    def test_normalized_coordinates_convert_to_original_pixels(self):
        self.assertEqual(pixel_point(Point(0.25, 0.5), 800, 400), (200.0, 200.0))

    def test_distance_accounts_for_image_aspect_ratio(self):
        distance = pixel_distance(Point(0.1, 0.2), Point(0.4, 0.6), 1000, 500)
        self.assertAlmostEqual(distance, (300**2 + 200**2) ** 0.5)


if __name__ == "__main__":
    unittest.main()
