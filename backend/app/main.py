"""Guard API: local authentication, database health, and fraud analysis."""

from datetime import datetime
from decimal import Decimal
import logging
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from .analysis import AnalysisEngine
from .analysis.knowledge import analyse_known_data
from .analysis.persistence import persist_outcome
from .auth import create_access_token, get_current_user, get_optional_user, hash_password, verify_password
from .config import get_settings
from .database import get_db
from .intelligence_routes import router as intelligence_router
from .models import AuditLog, Check, FraudReport, Profile, ReportStatus, User, UserRole

app = FastAPI(title="Guard Analysis API", version="0.2.0")
logger = logging.getLogger(__name__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(intelligence_router)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    role: str
    is_active: bool
    email_verified: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse


class AnalyseRequest(BaseModel):
    kind: Literal["message", "screenshot", "link", "number", "whatsapp", "payment", "call"]
    content: str = Field(min_length=1, max_length=20000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be blank")
        return value


class AnalyseResponse(BaseModel):
    level: Literal["Low Risk", "Caution", "High Risk", "Unable to Determine"]
    score: int = Field(ge=0, le=100)
    signals: list[str]
    explanation: str
    recommended_action: str
    pattern: str
    confidence: float = Field(ge=0, le=1)
    sources: list[str]
    check_id: str | None = None
    stored: bool
    evidence: list["EvidenceResponse"]
    provider_status: str
    provider_model: str | None


class EvidenceResponse(BaseModel):
    key: str
    label: str
    source: str
    confidence: float = Field(ge=0, le=1)
    contribution: int = Field(ge=0, le=100)
    evidence: str


class AdminCheckResponse(BaseModel):
    id: UUID
    check_type: str
    status: str
    content: str | None
    content_sha256: str | None
    risk_level: str | None
    risk_score: int | None
    pattern: str | None
    created_at: datetime


class HistoryResponse(BaseModel):
    id: UUID
    check_type: str
    status: str
    risk_level: str | None
    risk_score: int | None
    confidence: float | None
    pattern: str | None
    created_at: datetime


class ReportCreateRequest(BaseModel):
    description: str = Field(min_length=20, max_length=10000)
    entity_type: Literal["message", "link", "phone", "whatsapp", "payment", "other"] | None = None
    entity_value: str | None = Field(default=None, max_length=2048)
    amount_requested: Decimal | None = Field(default=None, ge=0)
    amount_lost: Decimal | None = Field(default=None, ge=0)
    incident_at: datetime | None = None

    @field_validator("description")
    @classmethod
    def description_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("description must not be blank")
        return value


class ReportResponse(BaseModel):
    id: UUID
    status: ReportStatus
    created_at: datetime


class AdminReportResponse(ReportResponse):
    reporter_id: UUID | None
    description: str
    entity_type: str | None
    entity_value: str | None
    amount_requested: Decimal | None
    amount_lost: Decimal | None
    incident_at: datetime | None


class ReportReviewRequest(BaseModel):
    status: Literal[
        "under_review",
        "verified_signal",
        "insufficient_evidence",
        "rejected",
        "archived",
    ]


analysis_engine = AnalysisEngine()
ANALYST_ROLES = {UserRole.super_admin, UserRole.fraud_analyst}


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.profile.full_name,
        role=user.profile.role.value,
        is_active=user.is_active,
        email_verified=user.email_verified,
    )


def require_analyst(user: User) -> None:
    if user.profile.role not in ANALYST_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Analyst access required")


@app.get("/health")
def health(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    try:
        db.execute(text("select 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from exc
    return {"status": "ok", "database": "connected"}


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/users", response_model=list[UserResponse], include_in_schema=False)
def get_all_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[UserResponse]:
    require_analyst(current_user)
    users = db.scalars(select(User).options(selectinload(User.profile))).all()
    return [user_response(user) for user in users]


@app.get("/v1/admin/checks", response_model=list[AdminCheckResponse])
def get_recent_checks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[AdminCheckResponse]:
    require_analyst(current_user)
    checks = db.scalars(
        select(Check)
        .options(selectinload(Check.analysis_result))
        .order_by(Check.created_at.desc())
        .limit(limit)
    ).all()
    return [
        AdminCheckResponse(
            id=check.id,
            check_type=check.check_type,
            status=check.status,
            content=check.input_metadata.get("content"),
            content_sha256=check.input_metadata.get("sha256"),
            risk_level=check.analysis_result.risk_level.value if check.analysis_result else None,
            risk_score=check.analysis_result.risk_score if check.analysis_result else None,
            pattern=check.analysis_result.likely_pattern if check.analysis_result else None,
            created_at=check.created_at,
        )
        for check in checks
    ]


@app.post("/v1/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> UserResponse:
    email = request.email.lower().strip()
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user = User(email=email, password_hash=hash_password(request.password))
    user.profile = Profile(full_name=request.full_name.strip())
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    db.refresh(user)
    return user_response(user)


@app.post("/v1/auth/login", response_model=TokenResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user = db.scalar(
        select(User)
        .options(selectinload(User.profile))
        .where(User.email == form.username.lower().strip())
    )
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    access_token, expires_in = create_access_token(user)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=user_response(user),
    )


@app.get("/v1/auth/me", response_model=UserResponse)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return user_response(current_user)


@app.get("/v1/history", response_model=list[HistoryResponse])
def history(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[HistoryResponse]:
    checks = db.scalars(
        select(Check)
        .options(selectinload(Check.analysis_result))
        .where(Check.user_id == current_user.id)
        .order_by(Check.created_at.desc())
        .limit(limit)
    ).all()
    return [
        HistoryResponse(
            id=check.id,
            check_type=check.check_type,
            status=check.status,
            risk_level=check.analysis_result.risk_level.value if check.analysis_result else None,
            risk_score=check.analysis_result.risk_score if check.analysis_result else None,
            confidence=(check.analysis_result.model_metadata.get("confidence")
                        if check.analysis_result else None),
            pattern=check.analysis_result.likely_pattern if check.analysis_result else None,
            created_at=check.created_at,
        )
        for check in checks
    ]


@app.post("/v1/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    request: ReportCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> ReportResponse:
    report = FraudReport(
        reporter_id=current_user.id if current_user else None,
        description=request.description,
        entity_type=request.entity_type,
        entity_value=request.entity_value.strip() if request.entity_value else None,
        amount_requested=request.amount_requested,
        amount_lost=request.amount_lost,
        incident_at=request.incident_at,
    )
    db.add(report)
    try:
        db.commit()
        db.refresh(report)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Fraud report could not be stored")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Report storage is temporarily unavailable",
        ) from exc
    return ReportResponse(id=report.id, status=report.status, created_at=report.created_at)


@app.get("/v1/admin/reports", response_model=list[AdminReportResponse])
def get_reports(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    report_status: Annotated[ReportStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[AdminReportResponse]:
    require_analyst(current_user)
    statement = select(FraudReport).order_by(FraudReport.created_at.desc()).limit(limit)
    if report_status is not None:
        statement = statement.where(FraudReport.status == report_status)
    reports = db.scalars(statement).all()
    return [
        AdminReportResponse(
            id=report.id,
            status=report.status,
            created_at=report.created_at,
            reporter_id=report.reporter_id,
            description=report.description,
            entity_type=report.entity_type,
            entity_value=report.entity_value,
            amount_requested=report.amount_requested,
            amount_lost=report.amount_lost,
            incident_at=report.incident_at,
        )
        for report in reports
    ]


@app.patch("/v1/admin/reports/{report_id}", response_model=AdminReportResponse)
def review_report(
    report_id: UUID,
    request: ReportReviewRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AdminReportResponse:
    require_analyst(current_user)
    report = db.get(FraudReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    previous_status = report.status.value
    report.status = ReportStatus(request.status)
    db.add(AuditLog(
        actor_id=current_user.id,
        action="fraud_report.status_changed",
        target_type="fraud_report",
        target_id=report.id,
        metadata_={"from": previous_status, "to": request.status},
    ))
    try:
        db.commit()
        db.refresh(report)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Fraud report review could not be stored")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Report review is temporarily unavailable",
        ) from exc
    return AdminReportResponse(
        id=report.id,
        status=report.status,
        created_at=report.created_at,
        reporter_id=report.reporter_id,
        description=report.description,
        entity_type=report.entity_type,
        entity_value=report.entity_value,
        amount_requested=report.amount_requested,
        amount_lost=report.amount_lost,
        incident_at=report.incident_at,
    )


@app.post("/v1/analyse", response_model=AnalyseResponse)
def analyse(
    request: AnalyseRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> AnalyseResponse:
    settings = get_settings()
    try:
        database_signals = analyse_known_data(db, settings, request.kind, request.content)
        outcome = analysis_engine.analyse(request.kind, request.content, database_signals)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    check_id = persist_outcome(
        db,
        request.kind,
        request.content,
        outcome,
        settings,
        user_id=current_user.id if current_user else None,
    )
    return AnalyseResponse(
        level=outcome.level,
        score=outcome.score,
        signals=[signal.label for signal in outcome.signals]
        or (["This analysis capability is not yet available in the MVP."]
            if outcome.level == "Unable to Determine"
            else ["No strong warning signal was found in the submitted content."]),
        explanation=outcome.explanation,
        recommended_action=outcome.recommended_action,
        pattern=outcome.pattern,
        confidence=outcome.confidence,
        sources=sorted({signal.source for signal in outcome.signals}),
        check_id=check_id,
        stored=check_id is not None,
        evidence=[
            EvidenceResponse(
                key=signal.key,
                label=signal.label,
                source=signal.source,
                confidence=signal.confidence,
                contribution=signal.contribution,
                evidence=signal.evidence,
            )
            for signal in outcome.signals
        ],
        provider_status=outcome.provider.status,
        provider_model=outcome.provider.model,
    )
