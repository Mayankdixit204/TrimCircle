import unittest

from app.models import RecommendationProfile
from app.recommender import load_catalog, recommend


class RecommenderTests(unittest.TestCase):
    def test_catalog_loads(self):
        self.assertGreaterEqual(len(load_catalog()), 10)

    def test_recommendations_are_ranked_and_limited(self):
        profile = RecommendationProfile(
            face_shape="round",
            texture="wavy",
            density="medium",
            current_length="medium",
            desired_length="medium",
            maintenance="low",
            limit=3,
        )
        results = recommend(profile)
        self.assertLessEqual(len(results), 3)
        self.assertEqual([item.score for item in results], sorted([item.score for item in results], reverse=True))
        self.assertTrue(all(item.reasons for item in results))

    def test_excluded_style_is_removed(self):
        profile = RecommendationProfile(
            face_shape="square",
            texture="straight",
            density="medium",
            current_length="short",
            desired_length="short",
            maintenance="low",
            excluded_styles=["buzz cut"],
        )
        self.assertNotIn("Buzz Cut", [item.name for item in recommend(profile)])

    def test_current_length_is_respected(self):
        profile = RecommendationProfile(
            face_shape="oval",
            texture="straight",
            density="high",
            current_length="short",
            desired_length="long",
            maintenance="medium",
        )
        self.assertEqual(recommend(profile), [])


if __name__ == "__main__":
    unittest.main()

