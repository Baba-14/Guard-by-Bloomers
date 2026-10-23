import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.main import app
from backend.app.models import Organization, PartnerApiKey, PartnerApiUsage, PartnerCustomer
from backend.app.partner_api import (
    PartnerPrincipal,
    api_key_hash,
    api_key_prefix,
    generate_api_key,
    get_partner_principal,
)


class FakeSession:
    def __init__(self):
        self.added = []
        self.scalar_calls = 0

    def scalar(self, statement):
        self.scalar_calls += 1
        return None if self.scalar_calls == 1 else 0

    def add(self, value):
        self.added.append(value)

    def commit(self):
        pass

    def rollback(self):
        pass


def settings():
    return SimpleNamespace(
        require_api_key_pepper=lambda: "partner-test-pepper-that-is-long-enough",
        analysis_database_lookup_enabled=False,
        analysis_persistence_enabled=False,
        store_analysis_content=False,
        jev_api_key="",
        jev_base_url="https://api.typesafe.ai",
        jev_model="jev-latest",
        jev_timeout_seconds=0.5,
    )


class PartnerApiTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession()
        self.organization = Organization(
            id=uuid4(),
            name="Pilot Bank",
            slug="pilot-bank",
            status="active",
            plan="pilot",
            monthly_check_quota=100,
        )
        self.api_key = PartnerApiKey(
            id=uuid4(),
            organization_id=self.organization.id,
            name="Test integration",
            prefix="guard_test_1234567890ab",
            secret_hash="0" * 64,
            environment="test",
            scopes=["checks:write"],
        )
        self.api_key.organization = self.organization
        self.principal = PartnerPrincipal(self.organization, self.api_key)
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_partner_principal] = lambda: self.principal
        self.settings_patch = patch("backend.app.partner_api.get_settings", return_value=settings())
        self.settings_patch.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.settings_patch.stop()
        app.dependency_overrides.clear()

    def test_generated_api_key_can_be_parsed_and_verified(self):
        prefix, secret, hashed = generate_api_key("test", settings())
        self.assertEqual(api_key_prefix(secret), prefix)
        self.assertEqual(api_key_hash(secret, settings()), hashed)
        self.assertNotIn(secret, hashed)

    def test_partner_check_returns_explainable_result_and_meters_usage(self):
        response = self.client.post(
            "/v1/checks",
            headers={"Idempotency-Key": "support-case-42"},
            json={
                "type": "message",
                "content": "Urgent: send your OTP now to reverse the MoMo payment.",
                "customer_reference": "customer-42",
                "metadata": {"channel": "support_chat"},
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["level"], "High Risk")
        self.assertIn("recommended_action", response.json())
        self.assertIsNotNone(response.headers.get("x-guard-request-id"))
        usage = next(item for item in self.db.added if isinstance(item, PartnerApiUsage))
        self.assertEqual(usage.organization_id, self.organization.id)
        self.assertEqual(usage.idempotency_key, "support-case-42")
        self.assertEqual(usage.customer_reference, "customer-42")
        customer = next(item for item in self.db.added if isinstance(item, PartnerCustomer))
        self.assertEqual(customer.external_reference, "customer-42")

    def test_partner_check_validates_blank_content(self):
        response = self.client.post("/v1/checks", json={"type": "message", "content": "  "})
        self.assertEqual(response.status_code, 422)

    def test_partner_check_rejects_blank_customer_reference(self):
        response = self.client.post(
            "/v1/checks",
            json={"type": "message", "content": "Please review this", "customer_reference": "  "},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
