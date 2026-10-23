import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.main import app
from backend.app.models import TelegramUpdateRecord


class FakeSession:
    def __init__(self):
        self.telegram_updates = {}

    def get(self, model, key):
        if model is TelegramUpdateRecord:
            return self.telegram_updates.get(key)
        return None

    def add(self, value):
        if isinstance(value, TelegramUpdateRecord):
            self.telegram_updates[value.update_id] = value

    def flush(self):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass


def settings():
    return SimpleNamespace(
        telegram_bot_token="test-token",
        telegram_webhook_secret="test-secret",
        telegram_allowed_group_ids=(-1001234567890,),
        telegram_api_base_url="https://api.telegram.test",
        telegram_timeout_seconds=0.5,
        analysis_database_lookup_enabled=False,
        analysis_persistence_enabled=False,
        store_analysis_content=False,
        jev_api_key="",
        jev_base_url="https://api.typesafe.ai",
        jev_model="jev-latest",
        jev_timeout_seconds=0.5,
    )


def update(text=None, *, update_id=101, chat_id=-1001234567890, caption=None, is_bot=False):
    message = {
        "message_id": 77,
        "chat": {"id": chat_id, "type": "supergroup"},
        "from": {"id": 42, "is_bot": is_bot},
    }
    if text is not None:
        message["text"] = text
    if caption is not None:
        message["caption"] = caption
    return {"update_id": update_id, "message": message}


class TelegramWebhookTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession()
        app.dependency_overrides[get_db] = lambda: self.db
        self.settings_patch = patch("backend.app.telegram.get_settings", return_value=settings())
        self.settings_patch.start()
        self.client = TestClient(app)
        self.headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}

    def tearDown(self):
        self.settings_patch.stop()
        app.dependency_overrides.clear()

    @patch("backend.app.telegram.send_warning", new_callable=AsyncMock)
    def test_safe_message_is_analysed_without_alert(self, send_warning):
        response = self.client.post(
            "/api/integrations/telegram/webhook",
            headers=self.headers,
            json=update("The community meeting starts at 6pm at the library."),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["classification"], "Low Risk")
        self.assertEqual(response.json()["alert"], "not_required")
        send_warning.assert_not_awaited()

    @patch("backend.app.telegram.send_warning", new_callable=AsyncMock)
    def test_suspicious_ghanaian_momo_message_gets_reply(self, send_warning):
        response = self.client.post(
            "/api/integrations/telegram/webhook",
            headers=self.headers,
            json=update("Urgent MoMo reversal: send your OTP and PIN now to reverse GH₵500."),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["classification"], "High Risk")
        self.assertEqual(response.json()["alert"], "delivered")
        send_warning.assert_awaited_once()

    @patch("backend.app.telegram.send_warning", new_callable=AsyncMock)
    def test_malicious_looking_url_in_caption_gets_alert(self, send_warning):
        response = self.client.post(
            "/api/integrations/telegram/webhook",
            headers=self.headers,
            json=update(caption="Your GCB account is locked. Verify at https://gcb-secure.vercel.app/login"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["classification"], "High Risk")
        send_warning.assert_awaited_once()

    @patch("backend.app.telegram.send_warning", new_callable=AsyncMock)
    def test_duplicate_update_is_not_processed_twice(self, send_warning):
        payload = update("Send your OTP immediately.")
        first = self.client.post("/api/integrations/telegram/webhook", headers=self.headers, json=payload)
        second = self.client.post("/api/integrations/telegram/webhook", headers=self.headers, json=payload)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.json(), {"status": "duplicate"})
        send_warning.assert_awaited_once()

    @patch("backend.app.telegram.send_warning", new_callable=AsyncMock)
    def test_unauthorized_group_is_ignored(self, send_warning):
        response = self.client.post(
            "/api/integrations/telegram/webhook",
            headers=self.headers,
            json=update("Send your OTP", chat_id=-1009999999999),
        )
        self.assertEqual(response.json()["reason"], "unauthorized_chat")
        send_warning.assert_not_awaited()

    def test_invalid_webhook_secret_is_rejected(self):
        response = self.client.post(
            "/api/integrations/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
            json=update("hello"),
        )
        self.assertEqual(response.status_code, 403)

    @patch("backend.app.telegram.send_warning", new_callable=AsyncMock)
    def test_telegram_api_failure_is_recorded_without_triggering_retry(self, send_warning):
        send_warning.side_effect = httpx.ConnectError("synthetic failure")
        response = self.client.post(
            "/api/integrations/telegram/webhook",
            headers=self.headers,
            json=update("Send your OTP immediately."),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["alert"], "failed")
        self.assertEqual(self.db.telegram_updates[101].alert_delivery_status, "failed")

    @patch("backend.app.telegram.send_warning", new_callable=AsyncMock)
    def test_missing_content_and_bot_messages_are_ignored(self, send_warning):
        missing = self.client.post(
            "/api/integrations/telegram/webhook", headers=self.headers, json=update()
        )
        bot = self.client.post(
            "/api/integrations/telegram/webhook",
            headers=self.headers,
            json=update("Send an OTP", update_id=102, is_bot=True),
        )
        self.assertEqual(missing.json()["reason"], "no_supported_content")
        self.assertEqual(bot.json()["reason"], "bot_message")
        send_warning.assert_not_awaited()

    def test_malformed_payload_is_rejected(self):
        response = self.client.post(
            "/api/integrations/telegram/webhook",
            headers=self.headers,
            json={"update_id": "not-an-integer", "message": {}},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
