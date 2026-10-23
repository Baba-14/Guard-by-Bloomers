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
from .auth import get_current_user, require_analyst
from .config import Settings, get_settings
from .database import get_db
from .models import Organization, OrganizationMember, PartnerApiKey, PartnerApiUsage, User


router = APIRouter(tags=["partner-api"])
CHECK_SCOPE = "checks:write"


def require_super_admin(user: User) -> None:
    if user.profile.role.value != "super_admin":
        raise HTTPException(status_code=403, detail="Super administrator access required")


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
    checks_this_month: int = 0
    active_keys: int = 0
    member_count: int = 0


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


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    environment: str
    prefix: str
    scopes: list[str]
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class OrganizationMemberRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: Literal["owner", "admin", "developer", "viewer"] = "viewer"


class OrganizationMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    full_name: str | None
    role: str
    created_at: datetime


class PartnerUsageResponse(BaseModel):
    request_id: UUID
    level: str | None
    score: int | None
    response_status: int
    created_at: datetime


class PartnerOverviewResponse(BaseModel):
    organization: OrganizationResponse
    membership_role: str
    total_checks: int
    checks_this_month: int
    remaining_this_month: int
    high_risk_this_month: int
    caution_this_month: int
    low_risk_this_month: int
    active_keys: int
    recent_usage: list[PartnerUsageResponse]
    keys: list[ApiKeyResponse]


@dataclass(frozen=True)
class PartnerPrincipal:
    organization: Organization
    api_key: PartnerApiKey


@dataclass(frozen=True)
class PartnerMemberPrincipal:
    user: User
    membership: OrganizationMember


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


def get_partner_member(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PartnerMemberPrincipal:
    membership = db.scalar(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.organization))
        .where(OrganizationMember.user_id == current_user.id)
        .order_by(OrganizationMember.created_at.asc())
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Partner workspace access is required")
    if membership.organization.status != "active":
        raise HTTPException(status_code=403, detail="Organization access is suspended")
    return PartnerMemberPrincipal(current_user, membership)


def _key_response(record: PartnerApiKey) -> ApiKeyResponse:
    return ApiKeyResponse(
        id=record.id,
        name=record.name,
        environment=record.environment,
        prefix=record.prefix,
        scopes=record.scopes,
        last_used_at=record.last_used_at,
        revoked_at=record.revoked_at,
        created_at=record.created_at,
    )


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
) -> OrganizationResponse:
    require_super_admin(current_user)
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
    return OrganizationResponse(
        id=organization.id, name=organization.name, slug=organization.slug,
        status=organization.status, plan=organization.plan,
        monthly_check_quota=organization.monthly_check_quota,
        created_at=organization.created_at,
    )


@router.get("/v1/admin/partners", response_model=list[OrganizationResponse])
def list_partners(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> list[OrganizationResponse]:
    require_super_admin(current_user)
    organizations = db.scalars(select(Organization).order_by(Organization.created_at.desc())).all()
    return [
        OrganizationResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            status=organization.status,
            plan=organization.plan,
            monthly_check_quota=organization.monthly_check_quota,
            created_at=organization.created_at,
            checks_this_month=_monthly_usage(db, organization.id),
            active_keys=int(db.scalar(select(func.count(PartnerApiKey.id)).where(
                PartnerApiKey.organization_id == organization.id,
                PartnerApiKey.revoked_at.is_(None),
            )) or 0),
            member_count=int(db.scalar(select(func.count(OrganizationMember.id)).where(
                OrganizationMember.organization_id == organization.id,
            )) or 0),
        )
        for organization in organizations
    ]


@router.post(
    "/v1/admin/partners/{organization_id}/members",
    response_model=OrganizationMemberResponse,
    status_code=201,
)
def add_partner_member(
    organization_id: UUID,
    request: OrganizationMemberRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> OrganizationMemberResponse:
    require_super_admin(current_user)
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    user = db.scalar(
        select(User).options(selectinload(User.profile)).where(User.email == request.email.lower().strip())
    )
    if user is None:
        raise HTTPException(status_code=404, detail="Create the Guard user before adding partner access")
    membership = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role=request.role,
    )
    db.add(membership)
    try:
        db.commit()
        db.refresh(membership)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This user already belongs to the organization") from exc
    return OrganizationMemberResponse(
        id=membership.id,
        user_id=user.id,
        email=user.email,
        full_name=user.profile.full_name,
        role=membership.role,
        created_at=membership.created_at,
    )


@router.get("/v1/admin/partners/{organization_id}/keys", response_model=list[ApiKeyResponse])
def list_partner_keys(
    organization_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> list[ApiKeyResponse]:
    require_super_admin(current_user)
    return [
        _key_response(record)
        for record in db.scalars(
            select(PartnerApiKey)
            .where(PartnerApiKey.organization_id == organization_id)
            .order_by(PartnerApiKey.created_at.desc())
        ).all()
    ]


@router.post("/v1/admin/partners/{organization_id}/keys", response_model=ApiKeyCreateResponse, status_code=201)
def create_partner_key(
    organization_id: UUID,
    request: ApiKeyCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> ApiKeyCreateResponse:
    require_super_admin(current_user)
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
    require_super_admin(current_user)
    record = db.get(PartnerApiKey, key_id)
    if record is None:
        raise HTTPException(status_code=404, detail="API key not found")
    record.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return Response(status_code=204)


@router.get("/v1/partner/overview", response_model=PartnerOverviewResponse)
def partner_overview(
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> PartnerOverviewResponse:
    organization = principal.membership.organization
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    monthly = list(db.scalars(
        select(PartnerApiUsage)
        .where(
            PartnerApiUsage.organization_id == organization.id,
            PartnerApiUsage.created_at >= month_start,
            PartnerApiUsage.response_status == 200,
        )
    ).all())
    recent = list(db.scalars(
        select(PartnerApiUsage)
        .where(PartnerApiUsage.organization_id == organization.id)
        .order_by(PartnerApiUsage.created_at.desc())
        .limit(20)
    ).all())
    keys = list(db.scalars(
        select(PartnerApiKey)
        .where(PartnerApiKey.organization_id == organization.id)
        .order_by(PartnerApiKey.created_at.desc())
    ).all())

    def risk_count(level: str) -> int:
        return sum(1 for item in monthly if item.response_payload.get("level") == level)

    return PartnerOverviewResponse(
        organization=OrganizationResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            status=organization.status,
            plan=organization.plan,
            monthly_check_quota=organization.monthly_check_quota,
            created_at=organization.created_at,
            checks_this_month=len(monthly),
            active_keys=sum(1 for key in keys if key.revoked_at is None),
            member_count=int(db.scalar(select(func.count(OrganizationMember.id)).where(
                OrganizationMember.organization_id == organization.id,
            )) or 0),
        ),
        membership_role=principal.membership.role,
        total_checks=int(db.scalar(select(func.count(PartnerApiUsage.id)).where(
            PartnerApiUsage.organization_id == organization.id,
            PartnerApiUsage.response_status == 200,
        )) or 0),
        checks_this_month=len(monthly),
        remaining_this_month=max(0, organization.monthly_check_quota - len(monthly)),
        high_risk_this_month=risk_count("High Risk"),
        caution_this_month=risk_count("Caution"),
        low_risk_this_month=risk_count("Low Risk"),
        active_keys=sum(1 for key in keys if key.revoked_at is None),
        recent_usage=[
            PartnerUsageResponse(
                request_id=item.request_id,
                level=item.response_payload.get("level"),
                score=item.response_payload.get("score"),
                response_status=item.response_status,
                created_at=item.created_at,
            )
            for item in recent
        ],
        keys=[_key_response(key) for key in keys],
    )


@router.post("/v1/partner/keys", response_model=ApiKeyCreateResponse, status_code=201)
def create_own_partner_key(
    request: ApiKeyCreateRequest,
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiKeyCreateResponse:
    if principal.membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Partner owner or administrator access required")
    prefix, secret, secret_hash = generate_api_key(request.environment, get_settings())
    record = PartnerApiKey(
        organization_id=principal.membership.organization_id,
        name=request.name.strip(),
        prefix=prefix,
        secret_hash=secret_hash,
        environment=request.environment,
        scopes=[CHECK_SCOPE],
        created_by=principal.user.id,
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


@router.post("/v1/partner/keys/{key_id}/revoke", status_code=204)
def revoke_own_partner_key(
    key_id: UUID,
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    if principal.membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Partner owner or administrator access required")
    record = db.get(PartnerApiKey, key_id)
    if record is None or record.organization_id != principal.membership.organization_id:
        raise HTTPException(status_code=404, detail="API key not found")
    record.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return Response(status_code=204)
