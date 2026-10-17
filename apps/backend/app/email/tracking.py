import hashlib
import hmac
import json
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import logger
from app.models.email import EmailMessage
from app.models.contact import Contact
from app.models.workspace import Workspace
from app.repositories.audit_repo import AuditRepository
from app.repositories.email_repo import EmailRepository
from app.repositories.lead_repo import LeadRepository


def verify_webhook_signature(
    raw_body: bytes,
    signature_header: Optional[str],
    secret_key: Optional[str] = None,
) -> bool:
    """
    Verifies HMAC-SHA256 signature for incoming provider webhooks.
    """
    secret = secret_key or settings.EMAIL_WEBHOOK_SECRET
    if not signature_header or not secret:
        return False

    computed = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    # Support "sha256=..." prefix or direct hex
    clean_sig = signature_header.replace("sha256=", "").strip()
    return hmac.compare_digest(computed.lower(), clean_sig.lower())


class WebhookTrackingProcessor:
    """
    Processes authenticated webhook events from email providers:
    - Ingests delivery, bounce, complaint, open, click, and unsubscribe events
    - Prevents replay attacks via event_id deduplication
    - Automatically adds bouncing or complaining recipients to the suppression list
    """

    async def process_event(
        self,
        session: AsyncSession,
        provider: str,
        event_id: str,
        event_type: str,
        recipient_email: str,
        provider_message_id: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        audit_repo = AuditRepository(session)
        email_repo = EmailRepository(session)
        lead_repo = LeadRepository(session)

        # 1. Deduplication check
        if await audit_repo.is_webhook_duplicate(event_id):
            logger.info(f"Duplicate webhook event ignored: {event_id}")
            return True

        payload_str = json.dumps(raw_payload or {}, default=str)
        await audit_repo.record_webhook_event(provider, event_id, payload_str)

        norm_email = recipient_email.strip().lower()

        # 2. Find associated email message
        message = None
        if provider_message_id:
            query = select(EmailMessage).where(EmailMessage.provider_message_id == provider_message_id)
            res = await session.execute(query)
            message = res.scalars().first()

        norm_event = event_type.upper()

        if message:
            # Record event on message
            await email_repo.record_event(message.id, norm_event, payload_str)
            if norm_event in {"BOUNCE", "BOUNCED"}:
                message.status = "BOUNCED"
            elif norm_event in {"COMPLAINT", "SPAM"}:
                message.status = "COMPLAINT"
            elif norm_event in {"DELIVERED", "DELIVERY"}:
                message.status = "DELIVERED"
            await session.flush()

        # 3. Automatic Suppression on Bounce, Complaint, or Unsubscribe
        if norm_event in {"BOUNCE", "BOUNCED", "COMPLAINT", "SPAM", "UNSUBSCRIBE", "UNSUBSCRIBED"}:
            workspace_id = message.workspace_id if message else None
            if not workspace_id and raw_payload:
                workspace_id = raw_payload.get("workspace_id")

            if not workspace_id:
                # Find contact's workspace
                contact_query = select(Contact).where(Contact.email == norm_email)
                c_res = await session.execute(contact_query)
                contact = c_res.scalars().first()
                if contact:
                    workspace_id = contact.workspace_id
                    contact.is_suppressed = True

            supp_reason = "BOUNCE" if "BOUNCE" in norm_event else ("COMPLAINT" if "COMPLAINT" in norm_event else "UNSUBSCRIBE")

            if workspace_id:
                await email_repo.add_suppression(
                    workspace_id=workspace_id,
                    email=norm_email,
                    reason=supp_reason,
                )
                logger.info(f"Recipient {norm_email} automatically added to suppression list ({norm_event}) for workspace {workspace_id}.")
            else:
                # Global fallback: suppress across all workspaces
                ws_res = await session.execute(select(Workspace.id))
                ws_ids = ws_res.scalars().all()
                for ws_id in ws_ids:
                    await email_repo.add_suppression(
                        workspace_id=ws_id,
                        email=norm_email,
                        reason=supp_reason,
                    )
                logger.info(f"Recipient {norm_email} automatically added to suppression list ({norm_event}) across all workspaces.")

                if message:
                    await lead_repo.log_activity(
                        workspace_id=workspace_id,
                        company_id=message.draft.contact.company_id if message.draft and message.draft.contact else "UNKNOWN",
                        contact_id=message.contact_id,
                        activity_type="STATUS_CHANGE",
                        details=f"Email delivery state updated: {norm_event}. Recipient suppressed.",
                        created_by="WEBHOOK_TRACKING_AGENT",
                    )

        return True


tracking_processor = WebhookTrackingProcessor()
