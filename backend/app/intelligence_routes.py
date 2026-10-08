"""Consent-aware collection, review and dataset administration routes."""

import csv
import hashlib
import hmac
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .auth import require_analyst
from .config import get_settings
from .database import get_db
from .intelligence import deidentify
from .models import (
    Brand, DatasetItem, DatasetLabel, DatasetSource, DatasetSourceType, FraudCategory,
    Feedback, FraudReport, PhoneIntelligence, ReviewQueueItem, ReviewStatus, UrlIntelligence, User,
)

router = APIRouter(prefix="/v1", tags=["Guard Intelligence"])
Db = Annotated[Session, Depends(get_db)]
Analyst = Annotated[User, Depends(require_analyst)]


class ReportRequest(BaseModel):
    report_type: str = Field(min_length=2, max_length=100)
    category: str = Field(min_length=2, max_length=100)
    identifier: str | None = Field(default=None, max_length=500)
    description: str = Field(min_length=10, max_length=20000)
    contribution_consent: Literal[True]
    consent_version: str = Field(default="guard-report-v1", max_length=50)
    country_code: str = Field(default="GH", min_length=2, max_length=2)
    channel: str | None = Field(default=None, max_length=50)


class ManualDatasetRequest(BaseModel):
    content: str = Field(min_length=2, max_length=20000)
    label: DatasetLabel = DatasetLabel.uncertain
    source_id: UUID
    category_id: UUID | None = None
    channel: str | None = None
    country_code: str | None = "GH"
    is_ghana_specific: bool = True
    language: str | None = "en"
    notes: str | None = None


class ReviewDecisionRequest(BaseModel):
    decision: DatasetLabel
    category_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=4000)
    approve: bool = True


class FeedbackRequest(BaseModel):
    helpful: bool
    kind: str = Field(min_length=2, max_length=30)
    result_level: str = Field(min_length=2, max_length=40)


def item_hash(content: str) -> str:
    return hashlib.sha256(" ".join(content.lower().split()).encode()).hexdigest()


def submission_fingerprint(host: str, at: datetime | None = None) -> str:
    """Return a rotating one-way identifier; the raw address is never stored."""
    day = (at or datetime.now(timezone.utc)).date().isoformat()
    secret = get_settings().require_jwt_secret().encode()
    return hmac.new(secret, f"{day}:{host}".encode(), hashlib.sha256).hexdigest()


def category_for(db: Session, value: str) -> FraudCategory | None:
    normalized = value.lower().strip().replace(" ", "-")
    return db.scalar(select(FraudCategory).where((FraudCategory.slug == normalized) | (func.lower(FraudCategory.name) == value.lower().strip())))


def serialize_item(item: DatasetItem) -> dict:
    return {
        "id": str(item.id), "content": item.content, "content_type": item.content_type,
        "channel": item.channel, "label": item.label.value, "category": item.category.name if item.category else None,
        "category_id": str(item.category_id) if item.category_id else None,
        "source": item.source.name, "source_type": item.source.source_type.value,
        "country_code": item.country_code, "is_ghana_specific": item.is_ghana_specific,
        "verification_status": item.verification_status.value, "privacy_status": item.privacy_status,
        "created_at": item.created_at,
    }


def create_candidate(
    db: Session, *, content: str, source: DatasetSource, label: DatasetLabel = DatasetLabel.uncertain,
    category_id: UUID | None = None, report_id: UUID | None = None, channel: str | None = None,
    country_code: str | None = "GH", is_ghana_specific: bool = True, consent: bool = False,
    metadata: dict | None = None,
) -> DatasetItem:
    clean_content, had_pii = deidentify(content)
    item = DatasetItem(
        content=clean_content, content_hash=item_hash(clean_content), channel=channel, label=label,
        category_id=category_id, source_id=source.id, fraud_report_id=report_id,
        country_code=country_code, is_ghana_specific=is_ghana_specific,
        verification_status=ReviewStatus.pending, contribution_consent=consent,
        privacy_status="deidentified" if had_pii else "reviewed_no_direct_pii",
        metadata_json=metadata or {},
    )
    db.add(item)
    db.flush()
    db.add(ReviewQueueItem(dataset_item_id=item.id, status=ReviewStatus.pending))
    return item


@router.post("/contributions", status_code=status.HTTP_201_CREATED)
def submit_report(payload: ReportRequest, http_request: Request, db: Db) -> dict:
    """Explicit reports contribute a de-identified candidate; ordinary checks never call this."""
    fingerprint = submission_fingerprint(http_request.client.host if http_request.client else "unknown")
    recent_count = db.scalar(
        select(func.count()).select_from(DatasetItem).where(
            DatasetItem.created_at >= datetime.now(timezone.utc) - timedelta(hours=1),
            DatasetItem.metadata_json["submission_fingerprint"].astext == fingerprint,
        )
    ) or 0
    if recent_count >= 5:
        raise HTTPException(status_code=429, detail="Too many reports from this connection. Please try again later.")

    category = category_for(db, payload.category)
    source = db.scalar(select(DatasetSource).where(DatasetSource.source_type == DatasetSourceType.user_report))
    if source is None:
        source = DatasetSource(name="Guard user reports", source_type=DatasetSourceType.user_report, description="Explicit user contributions")
        db.add(source)
        db.flush()
    report = FraudReport(
        category_id=category.id if category else None, description=payload.description,
        entity_type=payload.report_type, entity_value=payload.identifier,
        explicit_contribution_consent=True, consent_version=payload.consent_version,
        privacy_status="restricted_raw",
    )
    db.add(report)
    db.flush()
    try:
        create_candidate(
            db, content=payload.description, source=source,
            category_id=category.id if category else None, report_id=report.id,
            channel=payload.channel, country_code=payload.country_code.upper(),
            is_ghana_specific=payload.country_code.upper() == "GH", consent=True,
            metadata={"report_type": payload.report_type, "identifier_provided": bool(payload.identifier), "submission_fingerprint": fingerprint},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This report content is already awaiting review")
    return {"id": str(report.id), "reference": f"GRD-{str(report.id)[:8].upper()}", "status": "pending_review"}


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(payload: FeedbackRequest, db: Db) -> dict:
    """Store usefulness feedback without retaining the private checked content."""
    feedback = Feedback(
        helpful=payload.helpful,
        comment=f"kind={payload.kind}; result={payload.result_level}",
        contribution_consent=False,
    )
    db.add(feedback)
    db.commit()
    return {"id": str(feedback.id), "stored_content": False}


@router.get("/intelligence/overview")
def intelligence_overview(db: Db, _: Analyst) -> dict:
    counts = {label.value: db.scalar(select(func.count()).select_from(DatasetItem).where(DatasetItem.label == label)) or 0 for label in DatasetLabel}
    return {
        "total_items": db.scalar(select(func.count()).select_from(DatasetItem)) or 0,
        "pending_review": db.scalar(select(func.count()).select_from(ReviewQueueItem).where(ReviewQueueItem.status == ReviewStatus.pending)) or 0,
        "verified": db.scalar(select(func.count()).select_from(DatasetItem).where(DatasetItem.verification_status == ReviewStatus.verified)) or 0,
        "ghana_specific": db.scalar(select(func.count()).select_from(DatasetItem).where(DatasetItem.is_ghana_specific.is_(True))) or 0,
        "labels": counts,
    }


@router.get("/intelligence/review-queue")
def review_queue(db: Db, _: Analyst, queue_status: ReviewStatus = ReviewStatus.pending, limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    entries = db.scalars(
        select(ReviewQueueItem).options(
            selectinload(ReviewQueueItem.dataset_item).selectinload(DatasetItem.source),
            selectinload(ReviewQueueItem.dataset_item).selectinload(DatasetItem.category),
        ).where(ReviewQueueItem.status == queue_status).order_by(ReviewQueueItem.created_at).limit(limit)
    ).all()
    return [{"queue_id": str(entry.id), "status": entry.status.value, **serialize_item(entry.dataset_item)} for entry in entries]


@router.post("/intelligence/review-queue/{queue_id}/decision")
def review_decision(queue_id: UUID, request: ReviewDecisionRequest, db: Db, analyst: Analyst) -> dict:
    entry = db.scalar(select(ReviewQueueItem).options(selectinload(ReviewQueueItem.dataset_item)).where(ReviewQueueItem.id == queue_id))
    if entry is None:
        raise HTTPException(status_code=404, detail="Review item not found")
    if request.decision == DatasetLabel.fraud and request.category_id is None:
        raise HTTPException(status_code=422, detail="A fraud category is required for a verified fraud item")
    entry.decision = request.decision
    entry.category_id = request.category_id
    entry.notes = request.notes
    entry.reviewed_by = analyst.id
    entry.reviewed_at = datetime.now(timezone.utc)
    entry.status = ReviewStatus.verified if request.approve else ReviewStatus.rejected
    entry.dataset_item.label = request.decision
    entry.dataset_item.category_id = request.category_id
    entry.dataset_item.verification_status = entry.status
    db.commit()
    return {"queue_id": str(entry.id), "status": entry.status.value, "dataset_item_id": str(entry.dataset_item_id)}


@router.get("/intelligence/dataset")
def list_dataset(
    db: Db, _: Analyst, label: DatasetLabel | None = None, source_type: DatasetSourceType | None = None,
    verified: bool | None = None, ghana_specific: bool | None = None, query: str | None = None,
    limit: int = Query(100, ge=1, le=500),
) -> list[dict]:
    statement = select(DatasetItem).options(selectinload(DatasetItem.source), selectinload(DatasetItem.category)).order_by(DatasetItem.created_at.desc())
    if label: statement = statement.where(DatasetItem.label == label)
    if source_type: statement = statement.join(DatasetSource).where(DatasetSource.source_type == source_type)
    if verified is not None: statement = statement.where(DatasetItem.verification_status == (ReviewStatus.verified if verified else ReviewStatus.pending))
    if ghana_specific is not None: statement = statement.where(DatasetItem.is_ghana_specific == ghana_specific)
    if query: statement = statement.where(DatasetItem.content.ilike(f"%{query}%"))
    return [serialize_item(item) for item in db.scalars(statement.limit(limit)).all()]


@router.post("/intelligence/dataset", status_code=status.HTTP_201_CREATED)
def add_dataset_item(request: ManualDatasetRequest, db: Db, _: Analyst) -> dict:
    source = db.get(DatasetSource, request.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Dataset source not found")
    try:
        item = create_candidate(
            db, content=request.content, source=source, label=request.label,
            category_id=request.category_id, channel=request.channel, country_code=request.country_code,
            is_ghana_specific=request.is_ghana_specific, consent=True,
            metadata={"notes": request.notes} if request.notes else {},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A matching dataset item already exists")
    return {"id": str(item.id), "status": "pending_review"}


def parse_upload(filename: str, payload: bytes) -> list[dict]:
    extension = filename.lower().rsplit(".", 1)[-1]
    if extension == "json":
        decoded = json.loads(payload.decode("utf-8-sig"))
        return decoded if isinstance(decoded, list) else decoded.get("items", [])
    if extension == "csv":
        return list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    if extension == "xlsx":
        from openpyxl import load_workbook
        sheet = load_workbook(io.BytesIO(payload), read_only=True, data_only=True).active
        rows = sheet.iter_rows(values_only=True)
        headers = [str(value).strip() if value is not None else "" for value in next(rows)]
        return [dict(zip(headers, row)) for row in rows]
    raise HTTPException(status_code=415, detail="Upload a CSV, XLSX or JSON file")


@router.post("/intelligence/dataset/import", status_code=status.HTTP_201_CREATED)
async def import_dataset(db: Db, _: Analyst, source_id: UUID, file: UploadFile = File(...)) -> dict:
    source = db.get(DatasetSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Dataset source not found")
    payload = await file.read()
    if len(payload) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Dataset uploads are limited to 10 MB")
    try:
        rows = parse_upload(file.filename or "", payload)
    except (ValueError, json.JSONDecodeError, StopIteration) as error:
        raise HTTPException(status_code=422, detail=f"Could not parse dataset: {error}")
    imported, skipped, errors = 0, 0, []
    for index, row in enumerate(rows, start=2):
        content = str(row.get("content") or row.get("message") or "").strip()
        if not content:
            errors.append({"row": index, "error": "content/message is required"})
            continue
        raw_label = str(row.get("label") or row.get("fraud_status") or "uncertain").lower().strip()
        label = DatasetLabel(raw_label) if raw_label in {item.value for item in DatasetLabel} else DatasetLabel.uncertain
        category = category_for(db, str(row.get("category") or row.get("fraud_category") or "")) if (row.get("category") or row.get("fraud_category")) else None
        try:
            with db.begin_nested():
                create_candidate(
                    db, content=content, source=source, label=label,
                    category_id=category.id if category else None, channel=str(row.get("channel") or "") or None,
                    country_code=str(row.get("country") or row.get("country_code") or "").upper()[:2] or None,
                    is_ghana_specific=str(row.get("ghana_specific") or "").lower() in ("1", "true", "yes", "gh"),
                    consent=True, metadata={"import_file": file.filename, "import_row": index},
                )
            imported += 1
        except IntegrityError:
            skipped += 1
    db.commit()
    return {"imported": imported, "duplicates_skipped": skipped, "errors": errors[:100], "status": "pending_review"}


@router.get("/intelligence/categories")
def categories(db: Db, _: Analyst) -> list[dict]:
    return [{"id": str(item.id), "name": item.name, "slug": item.slug} for item in db.scalars(select(FraudCategory).order_by(FraudCategory.name)).all()]


@router.get("/intelligence/sources")
def sources(db: Db, _: Analyst) -> list[dict]:
    return [{"id": str(item.id), "name": item.name, "source_type": item.source_type.value, "description": item.description, "authoritative": item.is_authoritative} for item in db.scalars(select(DatasetSource).order_by(DatasetSource.name)).all()]


@router.get("/intelligence/brands")
def brands(db: Db, _: Analyst) -> list[dict]:
    return [{"id": str(item.id), "name": item.name, "country_code": item.country_code, "verified": item.verified, "official_domains": item.official_domains} for item in db.scalars(select(Brand).order_by(Brand.name)).all()]


@router.get("/intelligence/urls")
def urls(db: Db, _: Analyst, limit: int = Query(100, ge=1, le=500)) -> list[dict]:
    return [{"id": str(item.id), "url": item.url, "verdict": item.verdict.value, "risk_score": item.risk_score, "reports": item.report_count, "verified": item.verified} for item in db.scalars(select(UrlIntelligence).order_by(UrlIntelligence.risk_score.desc()).limit(limit)).all()]


@router.get("/intelligence/phone-numbers")
def phone_numbers(db: Db, _: Analyst, limit: int = Query(100, ge=1, le=500)) -> list[dict]:
    return [{"id": str(item.id), "sender_id": item.sender_id, "verdict": item.verdict.value, "risk_score": item.risk_score, "reports": item.report_count, "verified": item.verified} for item in db.scalars(select(PhoneIntelligence).order_by(PhoneIntelligence.risk_score.desc()).limit(limit)).all()]
