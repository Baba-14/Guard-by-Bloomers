"""Shared Guard Intelligence service used by web, mobile, extensions and partners."""

import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import DatasetLabel, PhoneIntelligence, UrlIntelligence


SIGNALS = {
    "otp": "OTP requested", "pin": "PIN or secret code requested",
    "password": "Password requested", "urgent": "Urgency or pressure to act",
    "immediately": "Urgency or pressure to act", "click": "Link or click-through request",
    "pay": "Payment request", "fee": "Advance fee or delivery charge",
    "guarantee": "Guaranteed return or reward", "suspend": "Account-suspension threat",
    "remote": "Remote-access request",
}
URL_PATTERN = re.compile(r"https?://[^\s<>\"]+|\b(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s<>\"]*)?", re.I)
PHONE_PATTERN = re.compile(r"(?:\+?233|0)[\s-]?(?:2\d|5\d)[\s-]?\d{3}[\s-]?\d{4}")
PII_PATTERNS = (
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[email removed]"),
    (PHONE_PATTERN, "[phone removed]"),
    (re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}(?:[ -]?\d{4})?\b"), "[number removed]"),
)


def normalize_url(value: str) -> str:
    candidate = value.strip().rstrip(".,;!?)]")
    if not candidate.lower().startswith(("http://", "https://")):
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{parsed.path or ''}".rstrip("/")


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    return f"+233{digits[1:]}" if digits.startswith("0") else f"+{digits}" if digits.startswith("233") else digits


def deidentify(text: str) -> tuple[str, bool]:
    cleaned, changed = text.strip(), False
    for pattern, replacement in PII_PATTERNS:
        cleaned, count = pattern.subn(replacement, cleaned)
        changed = changed or count > 0
    return cleaned, changed


@dataclass
class Analysis:
    level: Literal["Low Risk", "Caution", "High Risk", "Unable to Determine"]
    score: int
    signals: list[str]
    explanation: str
    recommended_action: str
    pattern: str
    components: dict[str, float | int | None]


def analyse_content(kind: str, content: str, db: Session | None = None) -> Analysis:
    """Fuse rules, the current text classifier signal, and curated reputation data.

    No submitted content is persisted here. Persistence only occurs through the
    explicit report/contribution endpoint.
    """
    lowered = content.lower()
    signals = list(dict.fromkeys(label for term, label in SIGNALS.items() if term in lowered))
    if kind == "screenshot":
        signals.append("Image submitted for contextual review")
    if kind in ("number", "whatsapp"):
        signals.append("Reputation data is moderated and does not identify a person as a fraudster")
    if kind == "whatsapp":
        signals.append("WhatsApp accounts can be taken over; verify unusual requests through another trusted channel")

    hosted_brand = kind == "link" and any(host in lowered for host in ("vercel.app", "netlify.app", "pages.dev")) and any(
        brand in lowered for brand in ("bank", "bnk", "gcb", "momo", "mtn", "ecobank", "login", "verify", "secure", "account")
    )
    if hosted_brand:
        signals.append("Brand-like name on a hosted subdomain")

    # This preserves the existing classifier as one signal boundary. Replace the
    # deterministic score with the deployed adapter without changing API clients.
    text_model_score = min(1.0, len(signals) * 0.18 + (0.15 if "http" in lowered else 0))
    url_score: int | None = None
    phone_score: int | None = None
    if db is not None:
        urls = URL_PATTERN.findall(content)
        if urls:
            known = db.scalar(select(UrlIntelligence).where(UrlIntelligence.normalized_url == normalize_url(urls[0])))
            if known:
                url_score = known.risk_score
                signals.append(f"Known URL intelligence: {known.verdict.value}")
        phones = PHONE_PATTERN.findall(content)
        if kind in ("number", "whatsapp") and not phones and content:
            phones = [content]
        if phones:
            # phone intelligence is linked to normalized phone_entities; a future
            # adapter can enrich unknown numbers without changing this service.
            known_phone = db.scalar(select(PhoneIntelligence).where(PhoneIntelligence.sender_id == normalize_phone(phones[0])))
            if known_phone:
                phone_score = known_phone.risk_score
                signals.append(f"Known sender intelligence: {known_phone.verdict.value}")

    rule_score = min(90, len(signals) * 18 + (15 if "http" in lowered else 0) + (28 if hosted_brand else 0))
    reputation_scores = [score for score in (url_score, phone_score) if score is not None]
    score = min(100, round(rule_score * 0.65 + text_model_score * 100 * 0.25 + (max(reputation_scores) if reputation_scores else 0) * 0.10))
    level = "High Risk" if score >= 60 else "Caution" if score >= 30 else "Low Risk" if score == 0 else "Unable to Determine"
    explanation = {
        "High Risk": "Strong fraud indicators were detected in the submitted information.",
        "Caution": "Some suspicious or unverifiable signals were detected.",
        "Low Risk": "No strong deterministic fraud signal was detected in the information submitted.",
        "Unable to Determine": "Not enough information was available to make a confident assessment.",
    }[level]
    action = (
        "Do not share OTPs, PINs or more money. Pause contact and verify through an official channel."
        if level == "High Risk" else
        "No strong warning sign was found, but still verify unexpected requests before acting."
        if level == "Low Risk" else "Pause before responding. Verify independently before acting."
    )
    pattern = (
        "Possible brand impersonation" if hosted_brand else
        "WhatsApp account reputation lookup" if kind == "whatsapp" else
        "Phone reputation lookup" if kind == "number" else
        "Suspicious link assessment" if kind == "link" else "Contextual fraud assessment"
    )
    return Analysis(level, score, signals or ["No deterministic warning signal was found in the submitted content."], explanation, action, pattern, {
        "text_model": round(text_model_score, 3), "rules": rule_score,
        "url_intelligence": url_score, "phone_reputation": phone_score,
    })
