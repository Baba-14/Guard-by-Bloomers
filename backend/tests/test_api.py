import unittest

from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.main import app


class DummySession:
    pass


def override_db():
    yield DummySession()


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def test_liveness_does_not_require_database(self):
        response = self.client.get("/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_public_analysis_returns_explainable_contract(self):
        response = self.client.post(
            "/v1/analyse",
            json={
                "kind": "message",
                "content": "Urgent: pay the processing fee and send your OTP immediately.",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["level"], "High Risk")
        self.assertGreaterEqual(body["score"], 55)
        self.assertFalse(body["stored"])
        self.assertIn("provider_status", body)
        self.assertTrue(body["evidence"])
        self.assertTrue(all("source" in item for item in body["evidence"]))

    def test_blank_analysis_is_rejected(self):
        response = self.client.post(
            "/v1/analyse",
            json={"kind": "message", "content": "   "},
        )
        self.assertEqual(response.status_code, 422)

    def test_unvalidated_mode_returns_unable_to_determine(self):
        response = self.client.post(
            "/v1/analyse",
            json={"kind": "screenshot", "content": "image.png"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["level"], "Unable to Determine")


if __name__ == "__main__":
    unittest.main()
