import unittest
from unittest.mock import patch

from backend.app import create_app


class AuthenticationRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-session-secret")
        self.client = self.app.test_client()

    def csrf_token(self):
        response = self.client.get("/api/auth/csrf")
        self.assertEqual(200, response.status_code)
        return response.get_json()["csrf_token"]

    def test_write_requests_require_csrf_and_protected_routes_require_login(self):
        response = self.client.post(
            "/api/auth/login",
            json={"identifier": "maya_chen", "password": "incorrect"},
        )
        self.assertEqual(400, response.status_code)
        self.assertIn("CSRF", response.get_json()["error"])
        self.assertEqual(401, self.client.get("/api/dashboard").status_code)

        token = self.csrf_token()
        with patch("backend.routes.api.get_user_for_auth", return_value=None):
            response = self.client.post(
                "/api/auth/login",
                json={"identifier": "unknown", "password": "not-the-password"},
                headers={"X-CSRF-Token": token},
            )
        self.assertEqual(401, response.status_code)
        self.assertEqual(
            {"authenticated": False},
            self.client.post(
                "/api/auth/logout",
                headers={"X-CSRF-Token": token},
            ).get_json(),
        )

    def test_account_cannot_read_or_write_another_accounts_data(self):
        token = self.csrf_token()
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["csrf_token"] = token

        current_user = {
            "user_id": 1,
            "username": "maya_chen",
            "email": "maya.chen@example.test",
            "display_name": "Maya Chen",
        }
        with patch("backend.routes.api.get_user", return_value=current_user):
            dashboard = self.client.get("/api/dashboard?user_id=2")
            saved = self.client.post(
                "/api/users/2/saved-items/1",
                headers={"X-CSRF-Token": token},
            )

        self.assertEqual(403, dashboard.status_code)
        self.assertEqual(403, saved.status_code)

    def test_registration_rejects_short_password_before_database_write(self):
        token = self.csrf_token()
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "new_user",
                "email": "new@example.test",
                "display_name": "New User",
                "password": "short",
            },
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(400, response.status_code)
        self.assertIn("12 and 128", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
