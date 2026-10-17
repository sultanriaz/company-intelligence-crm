import uuid
from typing import Optional
from app.core.logging import logger
from app.email.providers.base import BaseEmailProvider, ProviderSendResult


class MockEmailProvider(BaseEmailProvider):
    """
    Mock & Dry-Run email provider.
    Logs email parameters to console without sending outbound network requests.
    Used for local testing, CI, and when EMAIL_DRY_RUN=true.
    """

    name: str = "mock"

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str,
        from_address: str,
        from_name: str,
        reply_to: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> ProviderSendResult:
        mock_id = f"mock-msg-{uuid.uuid4().hex[:12]}"
        logger.info(
            f"[MOCK EMAIL DISPATCH] To: {to_email} | Subject: '{subject}' | "
            f"From: {from_name} <{from_address}> | IdempotencyKey: {idempotency_key} | MockMsgId: {mock_id}"
        )
        return ProviderSendResult(
            success=True,
            provider_name="mock",
            provider_message_id=mock_id,
            status="DRY_RUN",
            raw_response={"mock_id": mock_id, "recipient": to_email},
        )
