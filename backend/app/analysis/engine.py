"""Orchestrates analyzers and owns Guard's final risk decision."""

from collections import defaultdict
import re

from ..config import Settings, get_settings
from .jev import JevAnalyzer
from .rules import analyse_text
from .schemas import AnalysisOutcome, EvidenceSignal, ProviderMetadata
from .urls import analyse_url


EMBEDDED_URL_PATTERN = re.compile(
    r"https?://[^\s<>\"']+|\b(?:[a-z0-9-]+\.)+(?:com|org|net|app|dev|io|co|gh|info|xyz|invalid)(?:/[^\s<>\"']*)?",
    re.I,
)


PATTERNS = (
    ("credential", {"otp_request", "pin_request", "password_request", "card_security_code_request", "card_details_request", "identity_details_request", "jev_sensitive_request"}, "Possible credential theft"),
    ("advance", {"advance_payment", "jev_payment_request"}, "Possible advance-fee or payment scam"),
    ("investment", {"guaranteed_return", "investment_solicitation", "jev_category_investment_scam"}, "Possible prize or investment scam"),
    ("link", {"suspicious_domain", "punycode_domain", "ip_address_url", "url_credentials", "known_risky_domain", "known_risky_url"}, "Suspicious link assessment"),
    ("remote", {"remote_access_request"}, "Possible remote-access scam"),
    ("reversal", {"momo_reversal"}, "Possible Mobile Money reversal scam"),
    ("fake_payment", {"fake_payment_claim"}, "Possible fake payment confirmation"),
    ("takeover", {"account_takeover"}, "Possible account takeover"),
    ("impersonation", {"impersonation_claim", "unusual_payment_destination"}, "Possible impersonation scam"),
)

DEDUPE_GROUPS = {
    "otp_request": "credential_request",
    "pin_request": "credential_request",
    "password_request": "credential_request",
    "jev_sensitive_request": "credential_request",
    "card_security_code_request": "card_security_request",
    "card_details_request": "card_security_request",
    "urgency": "urgency",
    "fear_or_threat": "coercion",
    "jev_urgency": "urgency",
    "advance_payment": "payment_request",
    "jev_payment_request": "payment_request",
    "guaranteed_return": "promised_return",
    "jev_category_investment_scam": "promised_return",
}


class AnalysisEngine:
    def __init__(self, settings: Settings | None = None, jev: JevAnalyzer | None = None):
        self.settings = settings or get_settings()
        self.jev = jev or JevAnalyzer(self.settings)

    def analyse(
        self,
        kind: str,
        content: str,
        database_signals: list[EvidenceSignal] | None = None,
    ) -> AnalysisOutcome:
        supported_kinds = {"message", "screenshot", "link", "number", "whatsapp", "payment", "call"}
        if kind not in supported_kinds:
            raise ValueError("Unsupported analysis type")
        if kind == "screenshot" and len(re.findall(r"\b[A-Za-z]{2,}\b", content)) < 3:
            return AnalysisOutcome(
                level="Unable to Determine",
                score=0,
                confidence=0.0,
                signals=[],
                explanation="Not enough readable screenshot text was provided for a reliable assessment.",
                recommended_action="Try a clearer screenshot or paste the relevant visible text, then verify through an official channel.",
                pattern="Screenshot text review",
                provider=ProviderMetadata(provider="jev", model=self.settings.jev_model, status="disabled"),
            )
        signals = analyse_text(content)
        if kind == "link":
            signals.extend(analyse_url(content))
        else:
            # Inspect links wherever they appear, not only in the dedicated URL checker.
            for candidate in EMBEDDED_URL_PATTERN.findall(content)[:3]:
                signals.extend(analyse_url(candidate.rstrip(".,;!?)]}")))
        signals.extend(database_signals or [])

        # Number-only lookups should be decided by moderated reputation data, not
        # by asking a text classifier to infer risk from a phone number.
        if kind in {"number", "whatsapp"} and not re.search(r"[A-Za-z]{3,}", content):
            jev_signals = []
            provider = ProviderMetadata(provider="jev", model=self.settings.jev_model, status="disabled")
        else:
            jev_signals, provider = self.jev.analyse(content, kind)
        signals.extend(jev_signals)
        signals = self._deduplicate(signals)

        source_totals: dict[str, int] = defaultdict(int)
        for signal in signals:
            source_totals[signal.source] += signal.contribution
        # AI is supporting evidence. It cannot independently produce a high-risk verdict.
        source_totals["jev"] = min(source_totals["jev"], 30)
        score = min(100, sum(source_totals.values()))
        if score >= 55:
            level = "High Risk"
        elif score >= 20:
            level = "Caution"
        elif signals or kind in {"number", "whatsapp"}:
            level = "Unable to Determine"
        else:
            level = "Low Risk"

        confidence = self._confidence(signals, provider)
        return AnalysisOutcome(
            level=level,
            score=score,
            confidence=confidence,
            signals=signals,
            explanation=self._explanation(level, signals, provider, kind),
            recommended_action=self._action(level),
            pattern=self._pattern(signals, kind),
            provider=provider,
        )

    @staticmethod
    def _deduplicate(signals: list[EvidenceSignal]) -> list[EvidenceSignal]:
        strongest: dict[str, EvidenceSignal] = {}
        for signal in signals:
            group = DEDUPE_GROUPS.get(signal.key, signal.key)
            current = strongest.get(group)
            if current is None or signal.contribution > current.contribution:
                strongest[group] = signal
        return list(strongest.values())

    @staticmethod
    def _confidence(signals: list[EvidenceSignal], provider: ProviderMetadata) -> float:
        if not signals:
            return 0.45 if provider.status in {"disabled", "failed"} else 0.55
        independent_sources = len({signal.source for signal in signals})
        average = sum(signal.confidence for signal in signals) / len(signals)
        return round(min(0.98, average * (0.82 + 0.08 * independent_sources)), 2)

    @staticmethod
    def _explanation(level: str, signals: list[EvidenceSignal], provider: ProviderMetadata, kind: str) -> str:
        if not signals:
            if kind in {"number", "whatsapp"}:
                return "No verified reputation evidence was found for this number. That does not prove the caller or account is safe."
            suffix = " Jev was not used, so this result relies on local checks only." if provider.status != "used" else ""
            return "No strong warning signs were found, but this does not prove the submission is safe." + suffix
        top = sorted(signals, key=lambda item: item.contribution, reverse=True)[:2]
        reasons = "; ".join(signal.label for signal in top)
        if level == "High Risk":
            prefix = "Strong fraud indicators were detected"
        elif level == "Unable to Determine":
            prefix = "A warning sign was detected, but the evidence is not strong enough for a confident classification"
        else:
            prefix = "Warning signs were detected"
        return f"{prefix}. The strongest indicators are: {reasons}."

    @staticmethod
    def _action(level: str) -> str:
        if level == "High Risk":
            return "Do not send money or share an OTP, PIN, password, or verification code. Verify through an official channel."
        if level == "Caution":
            return "Pause and verify the sender, destination, and request through a separate trusted channel before acting."
        if level == "Unable to Determine":
            return "Do not rely on this result alone. Verify the request through a separate trusted or official channel."
        return "No strong warning sign was found. Still verify unexpected requests before paying, clicking, or sharing information."

    @staticmethod
    def _pattern(signals: list[EvidenceSignal], kind: str) -> str:
        keys = {signal.key for signal in signals}
        for _, candidates, label in PATTERNS:
            if keys & candidates:
                return label
        if kind == "link":
            return "Link risk review"
        if kind == "number":
            return "Phone reputation review"
        if kind == "whatsapp":
            return "WhatsApp account review"
        if kind == "payment":
            return "Payment request review"
        if kind == "call":
            return "Suspicious call review"
        if kind == "screenshot":
            return "Screenshot text review"
        return "Contextual fraud assessment"
