"""Telegram Bot API webhook handling for group fraud checks."""

from __future__ import annotations

from html import escape
import logging
import secrets
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .analysis import AnalysisEngine
from .analysis.knowledge import analyse_known_data
from .analysis.persistence import persist_outcome
from .config import Settings, get_settings
from .database import get_db
from .models import Check, TelegramUpdateRecord


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/integrations/telegram", tags=["integrations"])


class TelegramUser(BaseModel):
    id: int
    is_bot: bool = False


class TelegramChat(BaseModel):
    id: int
    type: str


class TelegramEntity(BaseModel):
    type: str
    offset: int = Field(ge=0)
    length: int = Field(ge=0)
    url: str | None = None


class TelegramMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message_id: int
    chat: TelegramChat
    sender: TelegramUser | None = Field(default=None, alias="from")
    text: str | None = None
    caption: str | None = None
    entities: list[TelegramEntity] = Field(default_factory=list)
    caption_entities: list[TelegramEntity] = Field(default_factory=list)


class TelegramUpdate(BaseModel):
    update_id: int
    message: TelegramMessage | None = None


def message_content(message: TelegramMessage) -> str | None:
    """Return text/caption plus entity URLs that Telegram does not show inline."""
    content = (message.text or message.caption or "").strip()
    entities = message.entities if message.text is not None else message.caption_entities
    hidden_urls = [entity.url for entity in entities if entity.type == "text_link" and entity.url]
    if hidden_urls:
        content = "\n".join([content, *hidden_urls]).strip()
    return content or None


def warning_html(outcome) -> str:
    signs = "\n".join(
        f"• {escape(signal.label)}"
        for signal in sorted(outcome.signals, key=lambda signal: signal.contribution, reverse=True)
    )
    level = escape(outcome.level.upper())
    action = escape(outcome.recommended_action)
    return (
        "🚨 <b>GUARD FRAUD ALERT</b>\n\n"
        f"Risk Level: <b>{level}</b>\n\n"
        "This message may be a scam.\n\n"
        f"<b>Warning Signs:</b>\n{signs}\n\n"
        f"<b>Recommended Action:</b>\n{action}\n\n"
        "🛡️ Protected by Guard"
    )


async def send_warning(
    settings: Settings, chat_id: int, message_id: int, outcome
) -> None:
    url = f"{settings.telegram_api_base_url}/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": warning_html(outcome),
        "parse_mode": "HTML",
        "reply_parameters": {
            "message_id": message_id,
            "allow_sending_without_reply": True,
        },
        "link_preview_options": {"is_disabled": True},
    }
    async with httpx.AsyncClient(timeout=settings.telegram_timeout_seconds) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        body = response.json()
        if body.get("ok") is not True:
            raise httpx.HTTPError("Telegram rejected sendMessage")


def _update_check_delivery(db: Session, check_id: str | None, delivery_status: str) -> None:
    if not check_id:
        return
    check = db.get(Check, UUID(check_id))
    if check is not None:
        check.input_metadata = {**check.input_metadata, "alert_delivery_status": delivery_status}


async def process_update(
    update: TelegramUpdate,
    db: Session,
    settings: Settings,
    engine: AnalysisEngine,
) -> dict[str, str]:
    message = update.message
    if message is None:
        return {"status": "ignored", "reason": "unsupported_update"}
    if message.chat.type not in {"group", "supergroup"} or message.chat.id not in settings.telegram_allowed_group_ids:
        return {"status": "ignored", "reason": "unauthorized_chat"}
    if message.sender is not None and message.sender.is_bot:
        return {"status": "ignored", "reason": "bot_message"}
    content = message_content(message)
    if content is None:
        return {"status": "ignored", "reason": "no_supported_content"}

    if db.get(TelegramUpdateRecord, update.update_id) is not None:
        return {"status": "duplicate"}
    receipt = TelegramUpdateRecord(
        update_id=update.update_id,
        chat_id=message.chat.id,
        message_id=message.message_id,
    )
    db.add(receipt)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return {"status": "duplicate"}

    try:
        database_signals = analyse_known_data(db, settings, "message", content)
        outcome = engine.analyse("message", content, database_signals)
        check_id = persist_outcome(
            db,
            "message",
            content,
            outcome,
            settings,
            source_metadata={
                "source": "telegram",
                "telegram_update_id": update.update_id,
                "telegram_chat_id": message.chat.id,
                "telegram_message_id": message.message_id,
                "alert_delivery_status": "pending" if outcome.level in {"Caution", "High Risk"} else "not_required",
            },
        )
        receipt.check_id = UUID(check_id) if check_id else None
        if outcome.level not in {"Caution", "High Risk"}:
            receipt.processing_status = "completed"
            receipt.alert_delivery_status = "not_required"
            db.commit()
            return {"status": "analysed", "classification": outcome.level, "alert": "not_required"}

        try:
            await send_warning(settings, message.chat.id, message.message_id, outcome)
            delivery_status = "delivered"
        except (httpx.HTTPError, ValueError):
            delivery_status = "failed"
            logger.warning(
                "Telegram alert delivery failed for update_id=%s chat_id=%s",
                update.update_id,
                message.chat.id,
            )
        receipt.processing_status = "completed"
        receipt.alert_delivery_status = delivery_status
        _update_check_delivery(db, check_id, delivery_status)
        db.commit()
        return {"status": "analysed", "classification": outcome.level, "alert": delivery_status}
    except Exception:
        db.rollback()
        logger.exception("Telegram update processing failed for update_id=%s", update.update_id)
        raise


@router.post("/webhook")
async def telegram_webhook(
    update: TelegramUpdate,
    db: Session = Depends(get_db),
    secret_token: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
) -> dict[str, str]:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram integration is not configured")
    if secret_token is None or not secrets.compare_digest(secret_token, settings.telegram_webhook_secret):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Telegram webhook secret")
    return await process_update(update, db, settings, AnalysisEngine(settings))
