import unittest
from unittest.mock import patch

from backend.engine.graph_recommender import recommend_for_user


def graph_snapshot():
    return {
        "interactions": [
            {"user_id": 1, "item_id": 10, "interaction_type": "click", "strength": 1},
            {"user_id": 2, "item_id": 10, "interaction_type": "like", "strength": 1},
            {"user_id": 2, "item_id": 11, "interaction_type": "purchase", "strength": 1},
            {"user_id": 3, "item_id": 12, "interaction_type": "purchase", "strength": 1},
        ],
        "ratings": [
            {"user_id": 1, "item_id": 13, "rating": 5},
            {"user_id": 2, "item_id": 10, "rating": 5},
        ],
        "saved_items": [
            {"user_id": 1, "item_id": 14},
        ],
        "interests": [
            {"user_id": 1, "category_id": 1, "interest_weight": 0.9},
        ],
        "categories": [
            {"category_id": 1, "parent_category_id": None, "name": "Books"},
            {"category_id": 2, "parent_category_id": 1, "name": "Data Science"},
            {"category_id": 3, "parent_category_id": None, "name": "Outdoor"},
        ],
        "items": [
            {
                "item_id": 10, "category_id": 2, "title": "Already viewed",
                "average_rating": 4.0, "rating_count": 1, "interaction_count": 3,
            },
            {
                "item_id": 11, "category_id": 2, "title": "Graph book",
                "average_rating": 4.5, "rating_count": 3, "interaction_count": 4,
            },
            {
                "item_id": 12, "category_id": 3, "title": "Popular pack",
                "average_rating": 4.8, "rating_count": 2, "interaction_count": 8,
            },
            {
                "item_id": 13, "category_id": 1, "title": "Already rated",
                "average_rating": 4.0, "rating_count": 1, "interaction_count": 1,
            },
            {
                "item_id": 14, "category_id": 1, "title": "Already saved",
                "average_rating": 4.0, "rating_count": 1, "interaction_count": 1,
            },
        ],
    }


class GraphRecommenderTests(unittest.TestCase):
    @patch("backend.engine.graph_recommender.save_recommendation_run")
    @patch("backend.engine.graph_recommender.load_graph_snapshot")
    def test_graph_rankings_skip_seen_items_and_record_run(self, load_snapshot, save_run):
        load_snapshot.return_value = graph_snapshot()

        result = recommend_for_user(1, limit=8)

        recommendations = result["recommendations"]
        self.assertEqual({11, 12}, {item["item_id"] for item in recommendations})
        graph_match = next(item for item in recommendations if item["item_id"] == 11)
        self.assertIn("similar activity", graph_match["reason"])
        self.assertTrue(all(0 <= item["score"] <= 1 for item in recommendations))
        self.assertEqual([1, 2], [item["rank_position"] for item in recommendations])
        load_snapshot.assert_called_once_with(1)
        saved_rows = save_run.call_args.args[0]
        self.assertEqual(2, len(saved_rows))
        self.assertTrue(all(row[0] == result["run_id"] for row in saved_rows))

    @patch("backend.engine.graph_recommender.save_recommendation_run")
    @patch("backend.engine.graph_recommender.load_graph_snapshot")
    def test_cold_profile_gets_a_community_fallback(self, load_snapshot, save_run):
        load_snapshot.return_value = graph_snapshot()

        result = recommend_for_user(99, limit=1)

        self.assertEqual(1, len(result["recommendations"]))
        self.assertEqual("Popular with the community", result["recommendations"][0]["reason"])
        self.assertGreaterEqual(result["recommendations"][0]["score"], 0)
        self.assertLessEqual(result["recommendations"][0]["score"], 1)
        save_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
