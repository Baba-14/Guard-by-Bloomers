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
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from .analysis import AnalysisEngine
from .analysis.knowledge import analyse_known_data
from .analysis.persistence import persist_outcome
from .auth import get_current_user, require_analyst
from .config import Settings, get_settings
from .database import get_db
from .models import AuditLog, Organization, OrganizationMember, PartnerApiKey, PartnerApiUsage, PartnerCustomer, User


router = APIRouter(tags=["partner-api"])
CHECK_SCOPE = "checks:write"
PartnerFeature = Literal["overview", "reports", "intelligence", "customers", "usage", "keys", "team"]


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

    @field_validator("customer_reference")
    @classmethod
    def customer_reference_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("customer_reference must not be blank")
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
    workspace_features: list[PartnerFeature] = Field(
        default_factory=lambda: ["overview", "reports", "intelligence", "customers", "usage", "keys", "team"],
        min_length=1,
    )


class OrganizationUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    plan: str | None = Field(default=None, min_length=2, max_length=40)
    status: Literal["active", "suspended"] | None = None
    monthly_check_quota: int | None = Field(default=None, ge=0, le=100_000_000)
    workspace_features: list[PartnerFeature] | None = Field(default=None, min_length=1)


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    plan: str
    monthly_check_quota: int
    workspace_features: list[PartnerFeature]
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


class OrganizationMemberUpdateRequest(BaseModel):
    role: Literal["owner", "admin", "developer", "viewer"]


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
    customer_reference: str | None = None
    api_key_prefix: str | None = None


class PartnerCustomerRequest(BaseModel):
    external_reference: str = Field(min_length=1, max_length=128)
    display_name: str | None = Field(default=None, max_length=160)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class PartnerCustomerUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=160)
    status: Literal["active", "suspended"] | None = None


class PartnerCustomerResponse(BaseModel):
    id: UUID
    external_reference: str
    display_name: str | None
    status: str
    checks_this_month: int
    high_risk_this_month: int
    last_active_at: datetime | None
    created_at: datetime


class PartnerAuditResponse(BaseModel):
    id: UUID
    action: str
    target_type: str | None
    target_id: UUID | None
    metadata: dict
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
    customer_count: int
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


def _organization_response(db: Session, organization: Organization) -> OrganizationResponse:
    return OrganizationResponse(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        status=organization.status,
        plan=organization.plan,
        monthly_check_quota=organization.monthly_check_quota,
        workspace_features=organization.workspace_features,
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


def _member_response(member: OrganizationMember, user: User) -> OrganizationMemberResponse:
    return OrganizationMemberResponse(
        id=member.id,
        user_id=user.id,
        email=user.email,
        full_name=user.profile.full_name,
        role=member.role,
        created_at=member.created_at,
    )


def _audit(
    db: Session,
    actor_id: UUID,
    action: str,
    target_type: str,
    target_id: UUID,
    metadata: dict | None = None,
) -> None:
    db.add(AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_=metadata or {},
    ))


def _customer_response(db: Session, customer: PartnerCustomer) -> PartnerCustomerResponse:
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    usage = list(db.scalars(
        select(PartnerApiUsage).where(
            PartnerApiUsage.organization_id == customer.organization_id,
            PartnerApiUsage.customer_reference == customer.external_reference,
            PartnerApiUsage.created_at >= month_start,
            PartnerApiUsage.response_status == 200,
        ).order_by(PartnerApiUsage.created_at.desc())
    ).all())
    return PartnerCustomerResponse(
        id=customer.id,
        external_reference=customer.external_reference,
        display_name=customer.display_name,
        status=customer.status,
        checks_this_month=len(usage),
        high_risk_this_month=sum(1 for item in usage if item.response_payload.get("level") == "High Risk"),
        last_active_at=usage[0].created_at if usage else None,
        created_at=customer.created_at,
    )


def _require_partner_manager(principal: PartnerMemberPrincipal) -> None:
    if principal.membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Partner owner or administrator access required")


def _require_partner_owner(principal: PartnerMemberPrincipal) -> None:
    if principal.membership.role != "owner":
        raise HTTPException(status_code=403, detail="Partner owner access required")


def _require_partner_feature(principal: PartnerMemberPrincipal, *features: PartnerFeature) -> None:
    enabled = set(principal.membership.organization.workspace_features or [])
    if not enabled.intersection(features):
        raise HTTPException(status_code=403, detail="This workspace section is not enabled")


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

    customer = None
    if request.customer_reference:
        customer = db.scalar(select(PartnerCustomer).where(
            PartnerCustomer.organization_id == principal.organization.id,
            PartnerCustomer.external_reference == request.customer_reference,
        ))
        if isinstance(customer, PartnerCustomer) and customer.status != "active":
            raise HTTPException(status_code=403, detail="Customer access is suspended")
        if not isinstance(customer, PartnerCustomer):
            db.add(PartnerCustomer(
                organization_id=principal.organization.id,
                external_reference=request.customer_reference,
            ))

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
        customer_reference=request.customer_reference,
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
        workspace_features=request.workspace_features,
    )
    db.add(organization)
    try:
        db.flush()
        _audit(db, current_user.id, "partner.created", "organization", organization.id, {
            "organization_id": str(organization.id),
            "plan": organization.plan,
            "monthly_check_quota": organization.monthly_check_quota,
        })
        db.commit()
        db.refresh(organization)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Organization slug is already in use") from exc
    return _organization_response(db, organization)


@router.get("/v1/admin/partners", response_model=list[OrganizationResponse])
def list_partners(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> list[OrganizationResponse]:
    require_super_admin(current_user)
    organizations = db.scalars(select(Organization).order_by(Organization.created_at.desc())).all()
    return [_organization_response(db, organization) for organization in organizations]


@router.get("/v1/admin/partners/{organization_id}", response_model=OrganizationResponse)
def get_partner(
    organization_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> OrganizationResponse:
    require_super_admin(current_user)
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return _organization_response(db, organization)


@router.patch("/v1/admin/partners/{organization_id}", response_model=OrganizationResponse)
def update_partner(
    organization_id: UUID,
    request: OrganizationUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> OrganizationResponse:
    require_super_admin(current_user)
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    changes = request.model_dump(exclude_none=True)
    for key, value in changes.items():
        setattr(organization, key, value.strip() if isinstance(value, str) else value)
    _audit(db, current_user.id, "partner.updated", "organization", organization.id, {"organization_id": str(organization.id), **changes})
    db.commit()
    db.refresh(organization)
    return _organization_response(db, organization)


@router.get(
    "/v1/admin/partners/{organization_id}/members",
    response_model=list[OrganizationMemberResponse],
)
def list_partner_members(
    organization_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> list[OrganizationMemberResponse]:
    require_super_admin(current_user)
    rows = db.execute(
        select(OrganizationMember, User)
        .join(User, User.id == OrganizationMember.user_id)
        .options(selectinload(User.profile))
        .where(OrganizationMember.organization_id == organization_id)
        .order_by(OrganizationMember.created_at.asc())
    ).all()
    return [_member_response(member, user) for member, user in rows]


@router.patch(
    "/v1/admin/partners/{organization_id}/members/{member_id}",
    response_model=OrganizationMemberResponse,
)
def update_partner_member(
    organization_id: UUID,
    member_id: UUID,
    request: OrganizationMemberUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> OrganizationMemberResponse:
    require_super_admin(current_user)
    member = db.get(OrganizationMember, member_id)
    if member is None or member.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Partner member not found")
    member.role = request.role
    user = db.scalar(select(User).options(selectinload(User.profile)).where(User.id == member.user_id))
    _audit(db, current_user.id, "partner.member_role_updated", "organization_member", member.id, {"organization_id": str(organization_id), "role": request.role})
    db.commit()
    assert user is not None
    return _member_response(member, user)


@router.delete("/v1/admin/partners/{organization_id}/members/{member_id}", status_code=204)
def remove_partner_member(
    organization_id: UUID,
    member_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> Response:
    require_super_admin(current_user)
    member = db.get(OrganizationMember, member_id)
    if member is None or member.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Partner member not found")
    _audit(db, current_user.id, "partner.member_removed", "organization_member", member.id, {"organization_id": str(organization_id)})
    db.delete(member)
    db.commit()
    return Response(status_code=204)


@router.get(
    "/v1/admin/partners/{organization_id}/customers",
    response_model=list[PartnerCustomerResponse],
)
def list_admin_partner_customers(
    organization_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> list[PartnerCustomerResponse]:
    require_super_admin(current_user)
    customers = db.scalars(select(PartnerCustomer).where(
        PartnerCustomer.organization_id == organization_id,
    ).order_by(PartnerCustomer.created_at.desc())).all()
    return [_customer_response(db, customer) for customer in customers]


@router.patch(
    "/v1/admin/partners/{organization_id}/customers/{customer_id}",
    response_model=PartnerCustomerResponse,
)
def update_admin_partner_customer(
    organization_id: UUID,
    customer_id: UUID,
    request: PartnerCustomerUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> PartnerCustomerResponse:
    require_super_admin(current_user)
    customer = db.get(PartnerCustomer, customer_id)
    if customer is None or customer.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Partner customer not found")
    changes = request.model_dump(exclude_none=True)
    for key, value in changes.items():
        setattr(customer, key, value)
    _audit(db, current_user.id, "partner.customer_updated", "partner_customer", customer.id, {"organization_id": str(organization_id), **changes})
    db.commit()
    return _customer_response(db, customer)


@router.get(
    "/v1/admin/partners/{organization_id}/usage",
    response_model=list[PartnerUsageResponse],
)
def list_admin_partner_usage(
    organization_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> list[PartnerUsageResponse]:
    require_super_admin(current_user)
    usage = db.scalars(select(PartnerApiUsage).where(
        PartnerApiUsage.organization_id == organization_id,
    ).order_by(PartnerApiUsage.created_at.desc()).limit(100)).all()
    keys = {key.id: key.prefix for key in db.scalars(select(PartnerApiKey).where(
        PartnerApiKey.organization_id == organization_id,
    )).all()}
    return [PartnerUsageResponse(
        request_id=item.request_id,
        level=item.response_payload.get("level"),
        score=item.response_payload.get("score"),
        response_status=item.response_status,
        created_at=item.created_at,
        customer_reference=item.customer_reference,
        api_key_prefix=keys.get(item.api_key_id),
    ) for item in usage]


@router.get(
    "/v1/admin/partners/{organization_id}/audit",
    response_model=list[PartnerAuditResponse],
)
def list_admin_partner_audit(
    organization_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> list[PartnerAuditResponse]:
    require_super_admin(current_user)
    records = db.scalars(select(AuditLog).where(or_(
        AuditLog.target_id == organization_id,
        AuditLog.metadata_["organization_id"].astext == str(organization_id),
    )).order_by(AuditLog.created_at.desc()).limit(100)).all()
    return [PartnerAuditResponse(
        id=record.id,
        action=record.action,
        target_type=record.target_type,
        target_id=record.target_id,
        metadata=record.metadata_,
        created_at=record.created_at,
    ) for record in records]


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
        db.flush()
        _audit(db, current_user.id, "partner.member_added", "organization_member", membership.id, {
            "organization_id": str(organization.id),
            "user_id": str(user.id),
            "role": request.role,
        })
        db.commit()
        db.refresh(membership)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This user already belongs to the organization") from exc
    return _member_response(membership, user)


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
    db.flush()
    _audit(db, current_user.id, "partner.key_created", "partner_api_key", record.id, {
        "organization_id": str(organization.id),
        "environment": request.environment,
        "prefix": prefix,
    })
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
    _audit(db, current_user.id, "partner.key_revoked", "partner_api_key", record.id, {
        "organization_id": str(record.organization_id),
        "prefix": record.prefix,
    })
    db.commit()
    return Response(status_code=204)


@router.get("/v1/partner/overview", response_model=PartnerOverviewResponse)
def partner_overview(
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> PartnerOverviewResponse:
    organization = principal.membership.organization
    features = set(organization.workspace_features or [])
    can_view_usage = bool(features.intersection({"overview", "reports", "intelligence", "usage"}))
    can_view_recent = bool(features.intersection({"overview", "reports", "usage"}))
    can_view_keys = "keys" in features
    can_view_customers = bool(features.intersection({"overview", "customers", "intelligence"}))
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    monthly = list(db.scalars(
        select(PartnerApiUsage)
        .where(
            PartnerApiUsage.organization_id == organization.id,
            PartnerApiUsage.created_at >= month_start,
            PartnerApiUsage.response_status == 200,
        )
    ).all()) if can_view_usage else []
    recent = list(db.scalars(
        select(PartnerApiUsage)
        .where(PartnerApiUsage.organization_id == organization.id)
        .order_by(PartnerApiUsage.created_at.desc())
        .limit(20)
    ).all()) if can_view_recent else []
    keys = list(db.scalars(
        select(PartnerApiKey)
        .where(PartnerApiKey.organization_id == organization.id)
        .order_by(PartnerApiKey.created_at.desc())
    ).all()) if can_view_keys else []
    key_prefixes = {key.id: key.prefix for key in keys}

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
            workspace_features=organization.workspace_features,
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
        )) or 0) if can_view_usage else 0,
        checks_this_month=len(monthly),
        remaining_this_month=max(0, organization.monthly_check_quota - len(monthly)),
        high_risk_this_month=risk_count("High Risk"),
        caution_this_month=risk_count("Caution"),
        low_risk_this_month=risk_count("Low Risk"),
        active_keys=sum(1 for key in keys if key.revoked_at is None),
        customer_count=int(db.scalar(select(func.count(PartnerCustomer.id)).where(
            PartnerCustomer.organization_id == organization.id,
        )) or 0) if can_view_customers else 0,
        recent_usage=[
            PartnerUsageResponse(
                request_id=item.request_id,
                level=item.response_payload.get("level"),
                score=item.response_payload.get("score"),
                response_status=item.response_status,
                created_at=item.created_at,
                customer_reference=item.customer_reference,
                api_key_prefix=key_prefixes.get(item.api_key_id),
            )
            for item in recent
        ],
        keys=[_key_response(key) for key in keys],
    )


@router.get("/v1/partner/members", response_model=list[OrganizationMemberResponse])
def list_own_partner_members(
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> list[OrganizationMemberResponse]:
    _require_partner_feature(principal, "team")
    rows = db.execute(
        select(OrganizationMember, User)
        .join(User, User.id == OrganizationMember.user_id)
        .options(selectinload(User.profile))
        .where(OrganizationMember.organization_id == principal.membership.organization_id)
        .order_by(OrganizationMember.created_at.asc())
    ).all()
    return [_member_response(member, user) for member, user in rows]


@router.post("/v1/partner/members", response_model=OrganizationMemberResponse, status_code=201)
def add_own_partner_member(
    request: OrganizationMemberRequest,
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationMemberResponse:
    _require_partner_feature(principal, "team")
    _require_partner_owner(principal)
    user = db.scalar(select(User).options(selectinload(User.profile)).where(
        User.email == request.email.lower().strip(),
    ))
    if user is None:
        raise HTTPException(status_code=404, detail="Create the Guard user before adding partner access")
    membership = OrganizationMember(
        organization_id=principal.membership.organization_id,
        user_id=user.id,
        role=request.role,
    )
    db.add(membership)
    try:
        db.flush()
        _audit(db, principal.user.id, "partner.member_added", "organization_member", membership.id, {
            "organization_id": str(principal.membership.organization_id),
            "user_id": str(user.id),
            "role": request.role,
        })
        db.commit()
        db.refresh(membership)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This user already belongs to the organization") from exc
    return _member_response(membership, user)


@router.patch("/v1/partner/members/{member_id}", response_model=OrganizationMemberResponse)
def update_own_partner_member(
    member_id: UUID,
    request: OrganizationMemberUpdateRequest,
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationMemberResponse:
    _require_partner_feature(principal, "team")
    _require_partner_owner(principal)
    member = db.get(OrganizationMember, member_id)
    if member is None or member.organization_id != principal.membership.organization_id:
        raise HTTPException(status_code=404, detail="Partner member not found")
    member.role = request.role
    user = db.scalar(select(User).options(selectinload(User.profile)).where(User.id == member.user_id))
    _audit(db, principal.user.id, "partner.member_role_updated", "organization_member", member.id, {
        "organization_id": str(principal.membership.organization_id),
        "role": request.role,
    })
    db.commit()
    assert user is not None
    return _member_response(member, user)


@router.delete("/v1/partner/members/{member_id}", status_code=204)
def remove_own_partner_member(
    member_id: UUID,
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    _require_partner_feature(principal, "team")
    _require_partner_owner(principal)
    member = db.get(OrganizationMember, member_id)
    if member is None or member.organization_id != principal.membership.organization_id:
        raise HTTPException(status_code=404, detail="Partner member not found")
    if member.id == principal.membership.id:
        raise HTTPException(status_code=400, detail="Transfer ownership before removing your own access")
    _audit(db, principal.user.id, "partner.member_removed", "organization_member", member.id, {
        "organization_id": str(principal.membership.organization_id),
    })
    db.delete(member)
    db.commit()
    return Response(status_code=204)


@router.get("/v1/partner/customers", response_model=list[PartnerCustomerResponse])
def list_own_partner_customers(
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PartnerCustomerResponse]:
    _require_partner_feature(principal, "customers", "intelligence")
    customers = db.scalars(select(PartnerCustomer).where(
        PartnerCustomer.organization_id == principal.membership.organization_id,
    ).order_by(PartnerCustomer.created_at.desc())).all()
    return [_customer_response(db, customer) for customer in customers]


@router.post("/v1/partner/customers", response_model=PartnerCustomerResponse, status_code=201)
def create_own_partner_customer(
    request: PartnerCustomerRequest,
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> PartnerCustomerResponse:
    _require_partner_feature(principal, "customers")
    _require_partner_manager(principal)
    customer = PartnerCustomer(
        organization_id=principal.membership.organization_id,
        external_reference=request.external_reference.strip(),
        display_name=request.display_name.strip() if request.display_name else None,
        metadata_=request.metadata,
    )
    db.add(customer)
    try:
        db.flush()
        _audit(db, principal.user.id, "partner.customer_created", "partner_customer", customer.id, {
            "organization_id": str(principal.membership.organization_id),
            "external_reference": customer.external_reference,
        })
        db.commit()
        db.refresh(customer)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This customer reference already exists") from exc
    return _customer_response(db, customer)


@router.patch("/v1/partner/customers/{customer_id}", response_model=PartnerCustomerResponse)
def update_own_partner_customer(
    customer_id: UUID,
    request: PartnerCustomerUpdateRequest,
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> PartnerCustomerResponse:
    _require_partner_feature(principal, "customers")
    _require_partner_manager(principal)
    customer = db.get(PartnerCustomer, customer_id)
    if customer is None or customer.organization_id != principal.membership.organization_id:
        raise HTTPException(status_code=404, detail="Partner customer not found")
    changes = request.model_dump(exclude_none=True)
    for key, value in changes.items():
        setattr(customer, key, value)
    _audit(db, principal.user.id, "partner.customer_updated", "partner_customer", customer.id, {
        "organization_id": str(principal.membership.organization_id),
        **changes,
    })
    db.commit()
    return _customer_response(db, customer)


@router.get("/v1/partner/usage", response_model=list[PartnerUsageResponse])
def list_own_partner_usage(
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PartnerUsageResponse]:
    _require_partner_feature(principal, "overview", "reports", "intelligence", "usage")
    organization_id = principal.membership.organization_id
    usage = db.scalars(select(PartnerApiUsage).where(
        PartnerApiUsage.organization_id == organization_id,
    ).order_by(PartnerApiUsage.created_at.desc()).limit(500)).all()
    keys = {key.id: key.prefix for key in db.scalars(select(PartnerApiKey).where(
        PartnerApiKey.organization_id == organization_id,
    )).all()}
    return [PartnerUsageResponse(
        request_id=item.request_id,
        level=item.response_payload.get("level"),
        score=item.response_payload.get("score"),
        response_status=item.response_status,
        created_at=item.created_at,
        customer_reference=item.customer_reference,
        api_key_prefix=keys.get(item.api_key_id),
    ) for item in usage]


@router.post("/v1/partner/keys", response_model=ApiKeyCreateResponse, status_code=201)
def create_own_partner_key(
    request: ApiKeyCreateRequest,
    principal: Annotated[PartnerMemberPrincipal, Depends(get_partner_member)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiKeyCreateResponse:
    _require_partner_feature(principal, "keys")
    _require_partner_manager(principal)
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
    db.flush()
    _audit(db, principal.user.id, "partner.key_created", "partner_api_key", record.id, {
        "organization_id": str(principal.membership.organization_id),
        "environment": request.environment,
        "prefix": prefix,
    })
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
    _require_partner_feature(principal, "keys")
    _require_partner_manager(principal)
    record = db.get(PartnerApiKey, key_id)
    if record is None or record.organization_id != principal.membership.organization_id:
        raise HTTPException(status_code=404, detail="API key not found")
    record.revoked_at = datetime.now(timezone.utc)
    _audit(db, principal.user.id, "partner.key_revoked", "partner_api_key", record.id, {
        "organization_id": str(principal.membership.organization_id),
        "prefix": record.prefix,
    })
    db.commit()
    return Response(status_code=204)
