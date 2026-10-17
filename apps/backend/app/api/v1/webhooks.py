import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tracking import tracking_agent
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.email.tracking import verify_webhook_signature
from app.schemas.webhook import WebhookResponse

router = APIRouter(prefix="/webhooks", tags=["Provider Webhooks Ingestion"])


@router.post("/email/{provider}", response_model=WebhookResponse)
async def ingest_email_provider_webhook(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_webhook_signature: str = Header(None, alias="X-Webhook-Signature"),
    signature: str = Header(None, alias="Signature"),
):
    """
    Ingests delivery, bounce, complaint, and unsubscribe webhooks from providers (Resend, SendGrid, SES).
    Cryptographically verifies HMAC signature and processes state transitions & auto-suppressions.
    """
    body_bytes = await request.body()
    sig = x_webhook_signature or signature

    # In production, signature verification is required
    if settings.APP_ENV == "production" or settings.EMAIL_WEBHOOK_SECRET != "dev-webhook-secret-signing-key":
        if not verify_webhook_signature(body_bytes, sig):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature.")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    # Normalize provider event format
    event_id = str(payload.get("id") or payload.get("event_id") or uuid.uuid4().hex)
    event_type = str(payload.get("type") or payload.get("event") or "DELIVERED").upper()
    recipient = str(payload.get("recipient") or payload.get("email") or payload.get("to") or "")
    provider_msg_id = payload.get("message_id") or payload.get("sg_message_id")

    # Delegate to EmailTrackingAgent
    success, _, err = await tracking_agent.run(
        session=db,
        provider=provider,
        event_id=event_id,
        event_type=event_type,
        recipient_email=recipient,
        provider_message_id=provider_msg_id,
        raw_payload=payload,
    )
    await db.commit()

    return WebhookResponse(
        status="received",
        event_id=event_id,
        processed=success if success is not None else False,
    )
