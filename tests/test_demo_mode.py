import os
import tempfile
import unittest
from unittest.mock import patch

from backend.app import create_app


class DemoModeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        database_path = os.path.join(self.temp_dir.name, "demo.sqlite3")
        with patch.dict(
            os.environ,
            {"DEMO_MODE": "true", "SQLITE_PATH": database_path},
        ):
            self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="demo-test-secret")
        self.client = self.app.test_client()

    def test_seeded_demo_supports_registration_recommendations_and_writes(self):
        health = self.client.get("/api/health")
        self.assertEqual(200, health.status_code)
        self.assertEqual("sqlite demo", health.get_json()["database"])

        categories = self.client.get("/api/categories")
        self.assertEqual(6, len(categories.get_json()["categories"]))

        csrf = self.client.get("/api/auth/csrf").get_json()["csrf_token"]
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "demo_user",
                "email": "demo@example.test",
                "display_name": "Demo User",
                "password": "Demonstration!2026",
            },
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(201, response.status_code)
        user = response.get_json()["user"]
        csrf = response.get_json()["csrf_token"]

        dashboard = self.client.get("/api/dashboard")
        self.assertEqual(200, dashboard.status_code)
        self.assertTrue(dashboard.get_json()["recommendations"])

        headers = {"X-CSRF-Token": csrf}
        saved_path = f"/api/users/{user['user_id']}/saved-items/1"
        self.assertEqual(200, self.client.post(saved_path, headers=headers).status_code)
        self.assertEqual(200, self.client.post(saved_path, headers=headers).status_code)

        rating_path = f"/api/users/{user['user_id']}/ratings"
        rating_body = {"item_id": 1, "rating": 5}
        self.assertEqual(
            200,
            self.client.post(rating_path, json=rating_body, headers=headers).status_code,
        )
        rating_body["rating"] = 4
        self.assertEqual(
            200,
            self.client.post(rating_path, json=rating_body, headers=headers).status_code,
        )


if __name__ == "__main__":
    unittest.main()
