import hashlib
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.email.compliance import compliance_service
from app.email.providers import get_email_provider
from app.models.email import EmailDraft, EmailMessage
from app.repositories.email_repo import EmailRepository
from app.repositories.lead_repo import LeadRepository
from app.schemas.contracts import EmailDeliveryResult


def generate_outbox_idempotency_key(workspace_id: str, contact_id: str, draft_id: str) -> str:
    """Generates unique deterministic SHA-256 idempotency key."""
    raw = f"{workspace_id}:{contact_id}:{draft_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class TransactionalOutboxService:
    """
    Manages guaranteed once-only outbound email delivery:
    - Enforces idempotency key constraints against double-sends
    - Validates compliance and suppression status
    - Interfaces with pluggable email providers
    - Updates delivery state and CRM activity timelines
    """

    async def stage_and_dispatch(
        self,
        session: AsyncSession,
        workspace_id: str,
        draft: EmailDraft,
        is_campaign_active: bool = True,
        is_approved: bool = False,
    ) -> EmailDeliveryResult:
        email_repo = EmailRepository(session)
        lead_repo = LeadRepository(session)

        # 1. Compliance check
        eligibility = await compliance_service.check_eligibility(
            session=session,
            workspace_id=workspace_id,
            recipient_email=draft.contact.email,
            is_campaign_active=is_campaign_active,
            auto_send_enabled=settings.EMAIL_AUTO_SEND_ENABLED,
            is_approved=is_approved or (draft.status == "APPROVED"),
        )

        if not eligibility.is_eligible:
            logger.warning(f"Email delivery rejected for {draft.contact.email}: {eligibility.rejection_reason}")
            return EmailDeliveryResult(
                message_id="",
                idempotency_key="",
                provider="none",
                delivery_status="REJECTED",
                error=eligibility.rejection_reason,
            )

        # 2. Idempotency & Double-Send Prevention
        idempotency_key = generate_outbox_idempotency_key(workspace_id, draft.contact_id, draft.id)
        existing_msg = await email_repo.get_by_idempotency_key(idempotency_key)

        if existing_msg:
            logger.warning(f"Double-send blocked by idempotency key: {idempotency_key}")
            return EmailDeliveryResult(
                message_id=existing_msg.id,
                idempotency_key=idempotency_key,
                provider=existing_msg.provider_name,
                provider_message_id=existing_msg.provider_message_id,
                delivery_status=existing_msg.status,
                error="Duplicate delivery prevented by idempotency constraint.",
            )

        # 3. Create outbox record in PENDING state
        provider = get_email_provider()
        message = await email_repo.create_message(
            workspace_id=workspace_id,
            contact_id=draft.contact_id,
            draft_id=draft.id,
            idempotency_key=idempotency_key,
            provider_name=provider.name,
        )

        # 4. Dispatch via configured provider
        send_result = await provider.send_email(
            to_email=draft.contact.email,
            subject=draft.subject,
            body_text=draft.body_text,
            body_html=draft.body_html,
            from_address=settings.EMAIL_FROM_ADDRESS,
            from_name=settings.EMAIL_FROM_NAME,
            reply_to=settings.EMAIL_REPLY_TO,
            idempotency_key=idempotency_key,
        )

        # 5. Update outbox record
        if send_result.success:
            message.status = send_result.status
            message.provider_message_id = send_result.provider_message_id
            message.sent_at = datetime.now(timezone.utc)
            draft.status = "SENT"

            # Record event
            await email_repo.record_event(
                message_id=message.id,
                event_type="DISPATCHED",
                payload_json=str(send_result.raw_response) if send_result.raw_response else None,
            )

            # Record CRM activity
            await lead_repo.log_activity(
                workspace_id=workspace_id,
                company_id=draft.contact.company_id,
                contact_id=draft.contact_id,
                activity_type="EMAIL_SENT",
                details=f"Outreach sent to {draft.contact.email}. Subject: '{draft.subject}' via {provider.name}.",
                created_by="EMAIL_OUTBOX_WORKER",
            )
        else:
            message.status = "FAILED"
            message.error_message = send_result.error_message
            draft.status = "FAILED"

        await session.flush()

        return EmailDeliveryResult(
            message_id=message.id,
            idempotency_key=idempotency_key,
            provider=provider.name,
            provider_message_id=message.provider_message_id,
            delivery_status=message.status,
            error=message.error_message,
        )


outbox_service = TransactionalOutboxService()
