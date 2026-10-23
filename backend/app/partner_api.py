"""Partner-facing API authentication, provisioning, metering, and fraud checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import re
import secrets
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from .analysis import AnalysisEngine
from .analysis.knowledge import analyse_known_data
from .analysis.persistence import persist_outcome
from .auth import require_analyst
from .config import Settings, get_settings
from .database import get_db
from .models import Organization, PartnerApiKey, PartnerApiUsage, User


router = APIRouter(tags=["partner-api"])
CHECK_SCOPE = "checks:write"


class PartnerCheckRequest(BaseModel):
    type: Literal["message", "screenshot", "link", "number", "whatsapp", "payment", "call"]
    content: str = Field(min_length=1, max_length=20000)
    customer_reference: str | None = Field(default=None, max_length=128)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be blank")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_small(cls, value: dict) -> dict:
        if len(value) > 20 or any(len(str(key)) > 64 or len(str(item)) > 256 for key, item in value.items()):
            raise ValueError("metadata supports at most 20 short key/value pairs")
        return value


class PartnerEvidenceResponse(BaseModel):
    key: str
    label: str
    source: str
    confidence: float
    contribution: int
    evidence: str


class PartnerCheckResponse(BaseModel):
    request_id: UUID
    level: Literal["Low Risk", "Caution", "High Risk", "Unable to Determine"]
    score: int
    signals: list[str]
    explanation: str
    recommended_action: str
    pattern: str
    confidence: float
    sources: list[str]
    check_id: str | None
    evidence: list[PartnerEvidenceResponse]


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    plan: str = Field(default="pilot", min_length=2, max_length=40)
    monthly_check_quota: int = Field(default=1000, ge=0, le=100_000_000)


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    plan: str
    monthly_check_quota: int
    created_at: datetime


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    environment: Literal["test", "live"] = "test"


class ApiKeyCreateResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    environment: str
    prefix: str
    secret: str
    created_at: datetime


@dataclass(frozen=True)
class PartnerPrincipal:
    organization: Organization
    api_key: PartnerApiKey


def api_key_hash(secret: str, settings: Settings) -> str:
    return sha256(f"{settings.require_api_key_pepper()}:{secret}".encode("utf-8")).hexdigest()


def generate_api_key(environment: Literal["test", "live"], settings: Settings) -> tuple[str, str, str]:
    prefix = f"guard_{environment}_{secrets.token_hex(6)}"
    secret = f"{prefix}_{secrets.token_urlsafe(32)}"
    return prefix, secret, api_key_hash(secret, settings)


def api_key_prefix(secret: str) -> str | None:
    match = re.fullmatch(r"(guard_(?:test|live)_[0-9a-f]{12})_[A-Za-z0-9_-]{32,}", secret)
    return match.group(1) if match else None


def get_partner_principal(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> PartnerPrincipal:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="A valid Guard API key is required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_error
    raw_key = authorization[7:].strip()
    prefix = api_key_prefix(raw_key)
    if prefix is None:
        raise credentials_error
    record = db.scalar(
        select(PartnerApiKey)
        .options(selectinload(PartnerApiKey.organization))
        .where(PartnerApiKey.prefix == prefix)
    )
    if record is None or not secrets.compare_digest(
        record.secret_hash, api_key_hash(raw_key, get_settings())
    ):
        raise credentials_error
    now = datetime.now(timezone.utc)
    if record.revoked_at is not None or (record.expires_at is not None and record.expires_at <= now):
        raise credentials_error
    if record.organization.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization access is suspended")
    if CHECK_SCOPE not in record.scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key lacks checks:write scope")
    record.last_used_at = now
    db.flush()
    return PartnerPrincipal(record.organization, record)


def _monthly_usage(db: Session, organization_id: UUID) -> int:
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    return int(db.scalar(
        select(func.count(PartnerApiUsage.id)).where(
            PartnerApiUsage.organization_id == organization_id,
            PartnerApiUsage.created_at >= month_start,
            PartnerApiUsage.response_status == 200,
        )
    ) or 0)


@router.post("/v1/checks", response_model=PartnerCheckResponse)
def partner_check(
    request: PartnerCheckRequest,
    response: Response,
    principal: Annotated[PartnerPrincipal, Depends(get_partner_principal)],
    db: Annotated[Session, Depends(get_db)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PartnerCheckResponse:
    if idempotency_key is not None:
        idempotency_key = idempotency_key.strip()
        if not idempotency_key or len(idempotency_key) > 160:
            raise HTTPException(status_code=400, detail="Idempotency-Key must contain 1 to 160 characters")
        previous = db.scalar(
            select(PartnerApiUsage).where(
                PartnerApiUsage.organization_id == principal.organization.id,
                PartnerApiUsage.idempotency_key == idempotency_key,
            )
        )
        if previous is not None:
            response.headers["X-Guard-Request-Id"] = str(previous.request_id)
            response.headers["Idempotent-Replayed"] = "true"
            return PartnerCheckResponse.model_validate(previous.response_payload)

    usage_before_request = _monthly_usage(db, principal.organization.id)
    if usage_before_request >= principal.organization.monthly_check_quota:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Organization monthly check quota has been reached",
            headers={"Retry-After": "3600"},
        )

    settings = get_settings()
    database_signals = analyse_known_data(db, settings, request.type, request.content)
    outcome = AnalysisEngine(settings).analyse(request.type, request.content, database_signals)
    check_id = persist_outcome(
        db,
        request.type,
        request.content,
        outcome,
        settings,
        source_metadata={
            "source": "partner_api",
            "organization_id": str(principal.organization.id),
            "api_key_id": str(principal.api_key.id),
            "customer_reference": request.customer_reference,
            "partner_metadata": request.metadata,
        },
    )
    request_id = uuid4()
    payload = PartnerCheckResponse(
        request_id=request_id,
        level=outcome.level,
        score=outcome.score,
        signals=[signal.label for signal in outcome.signals]
        or (["This analysis capability is not yet available."] if outcome.level == "Unable to Determine"
            else ["No strong warning signal was found in the submitted content."]),
        explanation=outcome.explanation,
        recommended_action=outcome.recommended_action,
        pattern=outcome.pattern,
        confidence=outcome.confidence,
        sources=sorted({signal.source for signal in outcome.signals}),
        check_id=check_id,
        evidence=[
            PartnerEvidenceResponse(
                key=signal.key,
                label=signal.label,
                source=signal.source,
                confidence=signal.confidence,
                contribution=signal.contribution,
                evidence=signal.evidence,
            )
            for signal in outcome.signals
        ],
    )
    db.add(PartnerApiUsage(
        organization_id=principal.organization.id,
        api_key_id=principal.api_key.id,
        check_id=UUID(check_id) if check_id else None,
        request_id=request_id,
        idempotency_key=idempotency_key,
        endpoint="/v1/checks",
        response_status=200,
        response_payload=payload.model_dump(mode="json"),
    ))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Idempotency key is already in use") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="API usage could not be recorded") from exc
    response.headers["X-Guard-Request-Id"] = str(request_id)
    response.headers["X-Guard-RateLimit-Limit"] = str(principal.organization.monthly_check_quota)
    response.headers["X-Guard-RateLimit-Remaining"] = str(
        max(0, principal.organization.monthly_check_quota - usage_before_request - 1)
    )
    return payload


@router.post("/v1/admin/partners", response_model=OrganizationResponse, status_code=201)
def create_partner(
    request: OrganizationCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> Organization:
    organization = Organization(
        name=request.name.strip(),
        slug=request.slug,
        plan=request.plan.strip(),
        monthly_check_quota=request.monthly_check_quota,
    )
    db.add(organization)
    try:
        db.commit()
        db.refresh(organization)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Organization slug is already in use") from exc
    return organization


@router.get("/v1/admin/partners", response_model=list[OrganizationResponse])
def list_partners(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> list[Organization]:
    return list(db.scalars(select(Organization).order_by(Organization.created_at.desc())).all())


@router.post("/v1/admin/partners/{organization_id}/keys", response_model=ApiKeyCreateResponse, status_code=201)
def create_partner_key(
    organization_id: UUID,
    request: ApiKeyCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> ApiKeyCreateResponse:
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    prefix, secret, secret_hash = generate_api_key(request.environment, get_settings())
    record = PartnerApiKey(
        organization_id=organization.id,
        name=request.name.strip(),
        prefix=prefix,
        secret_hash=secret_hash,
        environment=request.environment,
        scopes=[CHECK_SCOPE],
        created_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ApiKeyCreateResponse(
        id=record.id,
        organization_id=record.organization_id,
        name=record.name,
        environment=record.environment,
        prefix=record.prefix,
        secret=secret,
        created_at=record.created_at,
    )


@router.post("/v1/admin/partner-keys/{key_id}/revoke", status_code=204)
def revoke_partner_key(
    key_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> Response:
    record = db.get(PartnerApiKey, key_id)
    if record is None:
        raise HTTPException(status_code=404, detail="API key not found")
    record.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return Response(status_code=204)
