"""Jev decision provider. Failures are isolated from Guard's core analysis."""

import logging
from time import perf_counter
from typing import Any

import httpx

from ..config import Settings
from .schemas import EvidenceSignal, ProviderMetadata


logger = logging.getLogger(__name__)


QUESTIONS = {
    "fraud_category": {
        "type": "choice",
        "instructions": "Classify the most likely fraud pattern in this submission. Choose unknown when evidence is insufficient.",
        "criteria": {
            "credential_theft": "Requests passwords, PINs, OTPs, verification codes, or account access.",
            "advance_fee": "Requests payment before a prize, delivery, loan, job, grant, or benefit.",
            "impersonation": "Pretends to represent a trusted person, bank, telecom, government body, or business.",
            "investment_scam": "Promises implausible or guaranteed financial returns.",
            "account_takeover": "Uses a compromised account or asks the recipient to help regain or transfer access.",
            "unknown": "No category is adequately supported by the submission.",
        },
    },
    "risk": {
        "type": "score",
        "instructions": "Rate fraud risk using only evidence present in the submission.",
        "criteria": [
            "No observable fraud indicator",
            "Weak or ambiguous warning signs",
            "Multiple meaningful fraud indicators",
            "Strong evidence of a likely scam",
        ],
    },
    "requests_sensitive_information": {
        "type": "noul",
        "instructions": "Does the submission ask for a password, PIN, OTP, verification code, card data, or other account secret?",
        "criteria": {"true": "A secret or credential is requested.", "false": "No secret or credential is requested."},
    },
    "uses_urgency": {
        "type": "noul",
        "instructions": "Does the submission pressure the recipient to act before independently verifying the request?",
        "criteria": {"true": "It applies time pressure, threats, or artificial urgency.", "false": "It does not apply such pressure."},
    },
    "requests_payment": {
        "type": "noul",
        "instructions": "Does the submission request money, a fee, a transfer, or Mobile Money payment?",
        "criteria": {"true": "A payment or transfer is requested.", "false": "No payment or transfer is requested."},
    },
}


class JevAnalyzer:
    def __init__(self, settings: Settings):
        self.settings = settings

    def analyse(self, content: str, kind: str) -> tuple[list[EvidenceSignal], ProviderMetadata]:
        if not self.settings.jev_api_key:
            return [], ProviderMetadata(provider="jev", model=self.settings.jev_model, status="disabled")

        payload = {
            "model": self.settings.jev_model,
            "state": {"submission_type": kind, "content": content},
            "questions": QUESTIONS,
        }
        started_at = perf_counter()
        try:
            response = httpx.post(
                f"{self.settings.jev_base_url}/v1/systemone",
                headers={"Authorization": f"Bearer {self.settings.jev_api_key}"},
                json=payload,
                timeout=self.settings.jev_timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise TypeError("Jev returned a non-object response")
            answers = body.get("answers")
            if not isinstance(answers, dict) or not answers:
                raise ValueError("Jev response did not contain typed answers")
            signals = self._signals_from_answers(answers)
            return signals, ProviderMetadata(
                provider="jev",
                model=body.get("model", self.settings.jev_model),
                status="used",
                answers=answers,
                usage=body.get("usage", {}) if isinstance(body.get("usage"), dict) else {},
                latency_ms=round((perf_counter() - started_at) * 1000),
            )
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("Jev analysis unavailable: %s", exc)
            return [], ProviderMetadata(
                provider="jev",
                model=self.settings.jev_model,
                status="failed",
                latency_ms=round((perf_counter() - started_at) * 1000),
                error=type(exc).__name__,
            )

    @staticmethod
    def _answer(answers: Any, name: str) -> dict:
        if isinstance(answers, dict):
            value = answers.get(name, {})
            return value if isinstance(value, dict) else {}
        if isinstance(answers, list):
            return next((item for item in answers if isinstance(item, dict) and item.get("name") == name), {})
        return {}

    @staticmethod
    def _probability(answer: dict) -> float:
        for key in ("noul", "probability", "confidence"):
            value = answer.get(key)
            if isinstance(value, (int, float)):
                return max(0.0, min(1.0, float(value)))
        return 0.0

    def _signals_from_answers(self, answers: Any) -> list[EvidenceSignal]:
        signals: list[EvidenceSignal] = []
        mappings = (
            ("requests_sensitive_information", "jev_sensitive_request", "Jev detected a request for sensitive information", 22),
            ("uses_urgency", "jev_urgency", "Jev detected coercive urgency", 8),
            ("requests_payment", "jev_payment_request", "Jev detected a payment request", 10),
        )
        for question, key, label, weight in mappings:
            probability = self._probability(self._answer(answers, question))
            if probability >= 0.65:
                signals.append(EvidenceSignal(key, label, weight, probability, "jev", f"Jev probability: {probability:.0%}."))

        risk = self._answer(answers, "risk")
        raw_score = risk.get("score")
        confidence = self._probability(risk)
        if isinstance(raw_score, (int, float)) and float(raw_score) >= 1.5:
            normalized = min(1.0, max(0.0, float(raw_score) / 3.0))
            signals.append(EvidenceSignal("jev_risk", "Jev found contextual fraud risk", 18, max(confidence, normalized), "jev", f"Jev rubric score: {float(raw_score):.2f}/3."))

        category = self._answer(answers, "fraud_category")
        selected = category.get("choice") or category.get("value")
        category_confidence = self._probability(category)
        if selected and selected != "unknown" and category_confidence >= 0.55:
            label = str(selected).replace("_", " ").title()
            signals.append(EvidenceSignal(f"jev_category_{selected}", f"Jev category: {label}", 6, category_confidence, "jev", f"Jev category confidence: {category_confidence:.0%}."))
        return signals
