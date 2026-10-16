"""Moderated Guard database lookups used as independent analysis evidence."""

import logging
import re

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..config import Settings
from ..intelligence import PHONE_PATTERN, normalize_phone, normalize_url
from ..models import DatasetItem, DatasetLabel, DomainEntity, PhoneIntelligence, ReputationScore, ReviewStatus, UrlIntelligence
from .schemas import EvidenceSignal
from .rules import analyse_text
from .urls import extract_hostname


logger = logging.getLogger(__name__)

_STOPWORDS = {
    "about", "after", "again", "also", "been", "from", "have", "into", "just", "that",
    "their", "there", "these", "they", "this", "want", "what", "when", "with", "your",
}
_STRONG_REPORT_KEYS = {
    "otp_request", "pin_request", "password_request", "remote_access_request", "fake_payment_claim",
    "momo_reversal", "account_takeover", "guaranteed_return",
}


def _content_tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]{3,}", value.lower()) if token not in _STOPWORDS}


def analyse_report_patterns(db: Session, content: str) -> list[EvidenceSignal]:
    """Compare a check with consented report candidates and verified fraud items.

    Pending reports are deliberately low-weight context. Approved fraud reports carry
    more weight and are also promoted into exact URL/phone reputation tables.
    """
    current_tokens = _content_tokens(content)
    current_keys = {signal.key for signal in analyse_text(content)}
    if len(current_tokens) < 2 and not current_keys:
        return []
    try:
        item_result = db.scalars(
            select(DatasetItem).where(
                DatasetItem.contribution_consent.is_(True),
                DatasetItem.verification_status.in_([ReviewStatus.pending, ReviewStatus.verified]),
                DatasetItem.label.in_([DatasetLabel.fraud, DatasetLabel.uncertain]),
            ).order_by(DatasetItem.created_at.desc()).limit(300)
        )
        items = item_result.all()
        # Keep the lookup optional for lightweight callers that provide a
        # database stub rather than a SQLAlchemy ScalarResult.
        if not isinstance(items, list):
            return []
    except SQLAlchemyError as exc:
        db.rollback()
        logger.warning("Guard report-pattern lookup unavailable: %s", exc)
        return []

    verified_matches = 0
    pending_matches = 0
    matched_patterns: set[str] = set()
    for item in items:
        metadata = item.metadata_json if isinstance(item.metadata_json, dict) else {}
        report_keys = set(metadata.get("extracted_signals") or [])
        shared_keys = current_keys & report_keys
        token_overlap = current_tokens & _content_tokens(item.content)
        strong_match = bool(shared_keys & _STRONG_REPORT_KEYS and token_overlap)
        broad_match = len(shared_keys) >= 2 and len(token_overlap) >= 2
        phrase_match = len(token_overlap) >= 4 and bool(shared_keys)
        if not (strong_match or broad_match or phrase_match):
            continue
        matched_patterns.update(shared_keys)
        if item.verification_status == ReviewStatus.verified and item.label == DatasetLabel.fraud:
            verified_matches += 1
        else:
            pending_matches += 1

    signals: list[EvidenceSignal] = []
    if verified_matches:
        signals.append(EvidenceSignal(
            key="verified_report_pattern",
            label="Matches a verified fraud pattern from Guard reports",
            weight=min(42, 24 + verified_matches * 4),
            confidence=min(0.94, 0.72 + verified_matches * 0.04),
            source="database",
            evidence=(
                f"Similar to {verified_matches} verified report-derived pattern(s)"
                + (f" ({', '.join(sorted(matched_patterns)[:3])})." if matched_patterns else ".")
            ),
        ))
    if pending_matches:
        signals.append(EvidenceSignal(
            key="pending_report_pattern",
            label="Similar warning pattern appears in community reports awaiting review",
            weight=min(12, 5 + pending_matches),
            confidence=0.55,
            source="database",
            evidence=f"Similar to {pending_matches} consented report candidate(s) awaiting analyst review.",
        ))
    return signals


def analyse_known_data(
    db: Session,
    settings: Settings,
    kind: str,
    content: str,
) -> list[EvidenceSignal]:
    """Return only moderated reputation evidence; unreviewed reports never affect scores."""
    if not settings.analysis_database_lookup_enabled:
        return []

    report_signals = analyse_report_patterns(db, content)

    if kind in {"number", "whatsapp"}:
        phone_match = PHONE_PATTERN.search(content)
        if phone_match is None and kind == "whatsapp" and re.search(r"[A-Za-z]{3,}", content):
            return []
        normalized = normalize_phone(phone_match.group(0) if phone_match else content)
        if not normalized or len(re.sub(r"\D", "", normalized)) < 9:
            raise ValueError("Enter a valid Ghanaian or international phone number")
        try:
            known_phone = db.scalar(
                select(PhoneIntelligence).where(
                    PhoneIntelligence.sender_id == normalized,
                    PhoneIntelligence.verified.is_(True),
                )
            )
        except SQLAlchemyError as exc:
            db.rollback()
            logger.warning("Guard phone intelligence lookup unavailable: %s", exc)
            return report_signals
        if known_phone is None or not isinstance(known_phone.risk_score, int) or known_phone.risk_score < 20:
            return report_signals
        confidence = min(0.98, max(0.6, known_phone.risk_score / 100))
        return report_signals + [EvidenceSignal(
            key="known_risky_phone",
            label="Guard has verified risk evidence for this number",
            weight=min(80, max(20, known_phone.risk_score)),
            confidence=confidence,
            source="database",
            evidence=(
                f"Verified phone intelligence score {known_phone.risk_score}/100 from "
                f"{known_phone.report_count} reviewed report(s)."
            ),
        )]

    if kind != "link":
        return report_signals

    hostname = extract_hostname(content)
    try:
        known_url = db.scalar(
            select(UrlIntelligence).where(
                UrlIntelligence.normalized_url == normalize_url(content),
                UrlIntelligence.verified.is_(True),
            )
        )
        if known_url is not None and isinstance(known_url.risk_score, int) and known_url.risk_score >= 20:
            confidence = min(0.98, max(0.6, known_url.risk_score / 100))
            return report_signals + [EvidenceSignal(
                key="known_risky_url",
                label="Guard has verified risk evidence for this exact URL",
                weight=min(80, max(20, known_url.risk_score)),
                confidence=confidence,
                source="database",
                evidence=(
                    f"Verified URL intelligence score {known_url.risk_score}/100 from "
                    f"{known_url.report_count} reviewed report(s)."
                ),
            )]
        row = db.execute(
            select(DomainEntity, ReputationScore)
            .join(
                ReputationScore,
                and_(
                    ReputationScore.entity_type == "domain",
                    ReputationScore.entity_id == DomainEntity.id,
                ),
            )
            .where(
                func.lower(DomainEntity.domain) == hostname,
                ReputationScore.moderated.is_(True),
            )
        ).first()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.warning("Guard knowledge lookup unavailable: %s", exc)
        return []

    if row is None:
        return report_signals

    _, reputation = row
    if reputation.score < 20:
        return []

    contribution = min(40, max(10, round(reputation.score * 0.4)))
    confidence = min(0.98, max(0.5, reputation.score / 100))
    return report_signals + [
        EvidenceSignal(
            key="known_risky_domain",
            label="Guard has moderated risk evidence for this domain",
            weight=contribution,
            confidence=confidence,
            source="database",
            evidence=(
                f"Moderated reputation score {reputation.score}/100 from "
                f"{reputation.independent_reporters} independent reporter(s)."
            ),
        )
    ]
