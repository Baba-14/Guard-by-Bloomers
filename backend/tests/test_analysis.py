import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.app.analysis.engine import AnalysisEngine
from backend.app.analysis.jev import JevAnalyzer
from backend.app.analysis.knowledge import analyse_known_data
from backend.app.analysis.rules import analyse_text
from backend.app.analysis.schemas import EvidenceSignal, ProviderMetadata
from backend.app.analysis.urls import analyse_url
from backend.app.config import get_settings


class StubJev:
    def __init__(self, signals=None, status="disabled"):
        self.signals = signals or []
        self.status = status

    def analyse(self, content: str, kind: str):
        return self.signals, ProviderMetadata(provider="jev", model="test", status=self.status)


class AnalysisEngineTests(unittest.TestCase):
    def engine(self, signals=None, status="disabled") -> AnalysisEngine:
        return AnalysisEngine(get_settings(), jev=StubJev(signals, status))

    def test_high_risk_message_combines_independent_rules(self):
        result = self.engine().analyse(
            "message",
            "Urgent! You have won GH₵5,000. Pay a processing fee and send your OTP immediately.",
        )
        self.assertEqual(result.level, "High Risk")
        self.assertGreaterEqual(result.score, 55)
        self.assertIn("otp_request", {signal.key for signal in result.signals})
        self.assertIn("advance_payment", {signal.key for signal in result.signals})

    def test_word_boundaries_do_not_match_pin_inside_another_word(self):
        keys = {signal.key for signal in analyse_text("The spinning class begins tomorrow.")}
        self.assertNotIn("pin_request", keys)

    def test_shortened_url_is_caution_not_low_risk(self):
        result = self.engine().analyse("link", "https://bit.ly/example")
        self.assertEqual(result.level, "Caution")
        self.assertIn("shortened_url", {signal.key for signal in result.signals})

    def test_brand_name_on_hosted_subdomain_is_flagged(self):
        keys = {signal.key for signal in analyse_url("https://gcb-secure.vercel.app/login")}
        self.assertIn("suspicious_domain", keys)

    def test_jev_is_capped_as_supporting_evidence(self):
        signals = [
            EvidenceSignal("jev_sensitive_request", "Sensitive request", 50, 1.0, "jev", "test"),
            EvidenceSignal("jev_risk", "Contextual risk", 50, 1.0, "jev", "test"),
        ]
        result = self.engine(signals, "used").analyse("message", "Ambiguous message")
        self.assertEqual(result.score, 30)
        self.assertEqual(result.level, "Caution")

    def test_overlapping_local_and_jev_signals_are_not_double_counted(self):
        signals = [
            EvidenceSignal(
                "jev_sensitive_request",
                "Sensitive request",
                22,
                1.0,
                "jev",
                "test",
            )
        ]
        result = self.engine(signals, "used").analyse(
            "message",
            "Please send your OTP.",
        )
        credential_keys = {
            signal.key
            for signal in result.signals
            if signal.key in {"otp_request", "jev_sensitive_request"}
        }
        self.assertEqual(credential_keys, {"otp_request"})
        self.assertEqual(result.score, 35)

    def test_weak_warning_is_not_presented_as_low_risk(self):
        signals = [EvidenceSignal("weak", "Weak warning", 8, 0.7, "jev", "test")]
        result = self.engine(signals, "used").analyse("message", "Ambiguous message")
        self.assertEqual(result.level, "Unable to Determine")

    def test_database_and_local_evidence_can_produce_high_risk(self):
        database_signal = EvidenceSignal(
            "known_risky_domain",
            "Known risky domain",
            35,
            0.9,
            "database",
            "Moderated reputation evidence",
        )
        result = self.engine().analyse(
            "link",
            "http://192.0.2.10/login",
            database_signals=[database_signal],
        )
        self.assertEqual(result.level, "High Risk")
        self.assertIn("database", {signal.source for signal in result.signals})

    def test_low_risk_wording_does_not_claim_safety(self):
        result = self.engine().analyse("message", "Meeting moved to three o'clock.")
        self.assertEqual(result.level, "Low Risk")
        self.assertIn("does not prove", result.explanation)

    def test_jev_response_contract_becomes_supporting_signals(self):
        analyser = JevAnalyzer(get_settings())
        signals = analyser._signals_from_answers({
            "requests_sensitive_information": {"type": "noul", "noul": 0.91},
            "uses_urgency": {"type": "noul", "noul": 0.72},
            "requests_payment": {"type": "noul", "noul": 0.2},
            "risk": {"type": "score", "score": 2.4, "confidence": 0.84},
            "fraud_category": {"type": "choice", "choice": "credential_theft", "confidence": 0.88},
        })
        keys = {signal.key for signal in signals}
        self.assertIn("jev_sensitive_request", keys)
        self.assertIn("jev_risk", keys)
        self.assertIn("jev_category_credential_theft", keys)
        self.assertNotIn("jev_payment_request", keys)

    @patch("backend.app.analysis.jev.httpx.post")
    def test_jev_http_contract_uses_official_systemone_shape(self, post: Mock):
        post.return_value.raise_for_status.return_value = None
        post.return_value.json.return_value = {
            "model": "jev-2026-09-15",
            "answers": {
                "risk": {
                    "type": "score",
                    "score": 2.0,
                    "confidence": 0.8,
                    "legend": {},
                    "probabilities": {},
                }
            },
            "usage": {"input_tokens": 10, "output_tokens": 4},
        }
        settings = SimpleNamespace(
            jev_api_key="secret",
            jev_base_url="https://api.typesafe.ai",
            jev_model="jev-latest",
            jev_timeout_seconds=5,
        )
        signals, provider = JevAnalyzer(settings).analyse("Pay this fee", "message")
        self.assertEqual(provider.status, "used")
        self.assertEqual(provider.model, "jev-2026-09-15")
        self.assertEqual(provider.usage["input_tokens"], 10)
        self.assertIn("jev_risk", {signal.key for signal in signals})
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["model"], "jev-latest")
        self.assertEqual(payload["state"]["submission_type"], "message")
        self.assertIn("fraud_category", payload["questions"])

    @patch("backend.app.analysis.jev.httpx.post")
    def test_invalid_jev_response_falls_back_without_raising(self, post: Mock):
        post.return_value.raise_for_status.return_value = None
        post.return_value.json.return_value = {"model": "jev-latest", "answers": {}}
        settings = SimpleNamespace(
            jev_api_key="secret",
            jev_base_url="https://api.typesafe.ai",
            jev_model="jev-latest",
            jev_timeout_seconds=5,
        )
        signals, provider = JevAnalyzer(settings).analyse("hello", "message")
        self.assertEqual(signals, [])
        self.assertEqual(provider.status, "failed")

    def test_database_lookup_returns_only_moderated_reputation_evidence(self):
        reputation = SimpleNamespace(score=80, independent_reporters=3)
        result = Mock()
        result.first.return_value = (SimpleNamespace(domain="example.test"), reputation)
        db = Mock()
        db.execute.return_value = result
        settings = SimpleNamespace(analysis_database_lookup_enabled=True)
        signals = analyse_known_data(db, settings, "link", "https://example.test/pay")
        self.assertEqual([signal.key for signal in signals], ["known_risky_domain"])
        self.assertEqual(signals[0].source, "database")

    def test_non_mvp_mode_does_not_claim_low_risk(self):
        result = self.engine().analyse("screenshot", "image.png")
        self.assertEqual(result.level, "Unable to Determine")
        self.assertEqual(result.confidence, 0.0)
        self.assertIn("not part of", result.explanation)


if __name__ == "__main__":
    unittest.main()
