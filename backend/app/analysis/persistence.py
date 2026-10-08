"""Best-effort persistence for anonymous and authenticated fraud checks."""

from hashlib import sha256
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import AnalysisResultRecord, Check, CheckSignal, FraudSignal, RiskLevel
from .schemas import AnalysisOutcome


logger = logging.getLogger(__name__)

RISK_LEVELS = {
    "Low Risk": RiskLevel.low,
    "Caution": RiskLevel.caution,
    "High Risk": RiskLevel.high,
    "Unable to Determine": RiskLevel.unable_to_determine,
}


def persist_outcome(
    db: Session,
    kind: str,
    content: str,
    outcome: AnalysisOutcome,
    settings: Settings,
    user_id: UUID | None = None,
) -> str | None:
    """Store an analysis when PostgreSQL is available without breaking checks when it is not."""
    if not settings.analysis_persistence_enabled:
        return None

    metadata = {
        "sha256": sha256(content.encode("utf-8")).hexdigest(),
        "length": len(content),
    }
    if settings.store_analysis_content:
        metadata["content"] = content

    try:
        check = Check(
            user_id=user_id,
            check_type=kind,
            input_metadata=metadata,
            status="analysed",
        )
        check.analysis_result = AnalysisResultRecord(
            risk_level=RISK_LEVELS[outcome.level],
            risk_score=outcome.score,
            likely_pattern=outcome.pattern,
            explanation=outcome.explanation,
            recommended_action=outcome.recommended_action,
            model_metadata={
                "confidence": outcome.confidence,
                "provider": {
                    "name": outcome.provider.provider,
                    "model": outcome.provider.model,
                    "status": outcome.provider.status,
                    "answers": outcome.provider.answers,
                    "usage": outcome.provider.usage,
                    "latency_ms": outcome.provider.latency_ms,
                    "error": outcome.provider.error,
                },
                "signals": [
                    {
                        "key": signal.key,
                        "source": signal.source,
                        "confidence": signal.confidence,
                        "weight": signal.weight,
                        "contribution": signal.contribution,
                        "evidence": signal.evidence,
                    }
                    for signal in outcome.signals
                ],
            },
        )
        db.add(check)
        db.flush()

        keys = {signal.key for signal in outcome.signals}
        known = {
            signal.key: signal
            for signal in db.scalars(
                select(FraudSignal).where(FraudSignal.key.in_(keys), FraudSignal.active.is_(True))
            )
        } if keys else {}
        for evidence in outcome.signals:
            stored_signal = known.get(evidence.key)
            if stored_signal:
                db.add(
                    CheckSignal(
                        check_id=check.id,
                        signal_id=stored_signal.id,
                        evidence=evidence.evidence,
                        weight_applied=evidence.contribution,
                    )
                )
        db.commit()
        return str(check.id)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.warning("Analysis was returned but could not be persisted: %s", exc)
        return None
