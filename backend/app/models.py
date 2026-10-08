"""ORM mappings for authentication, analysis, reputation, and review data."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserRole(str, Enum):
    user = "user"
    super_admin = "super_admin"
    fraud_analyst = "fraud_analyst"
    support_admin = "support_admin"


class RiskLevel(str, Enum):
    low = "low"
    caution = "caution"
    high = "high"
    unable_to_determine = "unable_to_determine"


class ReportStatus(str, Enum):
    submitted = "submitted"
    under_review = "under_review"
    verified_signal = "verified_signal"
    insufficient_evidence = "insufficient_evidence"
    rejected = "rejected"
    appealed = "appealed"
    archived = "archived"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped["Profile"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    full_name: Mapped[str | None] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, name="user_role", create_type=False), default=UserRole.user
    )
    privacy_preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="profile")


class Check(Base):
    __tablename__ = "checks"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    check_type: Mapped[str] = mapped_column(Text)
    input_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(Text, default="analysed")
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    analysis_result: Mapped["AnalysisResultRecord"] = relationship(
        back_populates="check", cascade="all, delete-orphan", uselist=False
    )


class AnalysisResultRecord(Base):
    __tablename__ = "analysis_results"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    check_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("checks.id", ondelete="CASCADE"), unique=True
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        SqlEnum(RiskLevel, name="risk_level", create_type=False)
    )
    risk_score: Mapped[int] = mapped_column(Integer)
    likely_pattern: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    recommended_action: Mapped[str | None] = mapped_column(Text)
    model_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    check: Mapped[Check] = relationship(back_populates="analysis_result")


class FraudSignal(Base):
    __tablename__ = "fraud_signals"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    weight: Mapped[int] = mapped_column(Integer, default=10)
    severity: Mapped[str] = mapped_column(Text, default="medium")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FraudCategory(Base):
    __tablename__ = "fraud_categories"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, unique=True)
    slug: Mapped[str] = mapped_column(Text, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CheckSignal(Base):
    __tablename__ = "check_signals"

    check_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("checks.id", ondelete="CASCADE"), primary_key=True
    )
    signal_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("fraud_signals.id", ondelete="CASCADE"), primary_key=True
    )
    evidence: Mapped[str | None] = mapped_column(Text)
    weight_applied: Mapped[int | None] = mapped_column(Integer)


class DomainEntity(Base):
    __tablename__ = "domain_entities"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    domain: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReputationScore(Base):
    __tablename__ = "reputation_scores"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(Text)
    entity_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    report_count: Mapped[int] = mapped_column(Integer, default=0)
    independent_reporters: Mapped[int] = mapped_column(Integer, default=0)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=0)
    moderated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FraudReport(Base):
    __tablename__ = "fraud_reports"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    reporter_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    category_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("fraud_categories.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ReportStatus] = mapped_column(
        SqlEnum(ReportStatus, name="report_status", create_type=False), default=ReportStatus.submitted
    )
    description: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str | None] = mapped_column(Text)
    entity_value: Mapped[str | None] = mapped_column(Text)
    amount_requested: Mapped[Decimal | None] = mapped_column(Numeric)
    amount_lost: Mapped[Decimal | None] = mapped_column(Numeric)
    incident_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    actor_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(Text)
    target_type: Mapped[str | None] = mapped_column(Text)
    target_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
