"""Moderated Guard database lookups used as independent analysis evidence."""

import logging

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import DomainEntity, ReputationScore
from .schemas import EvidenceSignal
from .urls import extract_hostname


logger = logging.getLogger(__name__)


def analyse_known_data(
    db: Session,
    settings: Settings,
    kind: str,
    content: str,
) -> list[EvidenceSignal]:
    """Return only moderated reputation evidence; unreviewed reports never affect scores."""
    if not settings.analysis_database_lookup_enabled or kind != "link":
        return []

    hostname = extract_hostname(content)
    try:
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
        return []

    _, reputation = row
    if reputation.score < 20:
        return []

    contribution = min(40, max(10, round(reputation.score * 0.4)))
    confidence = min(0.98, max(0.5, reputation.score / 100))
    return [
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
