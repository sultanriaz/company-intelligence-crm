from typing import Any, Dict, Optional
from pydantic import BaseModel


class ProviderSendResult(BaseModel):
    success: bool
    provider_name: str
    provider_message_id: Optional[str] = None
    status: str  # SENT, DRY_RUN, REJECTED, FAILED
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class BaseEmailProvider:
    """Interface for outbound email service providers."""

    name: str = "base"

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
        raise NotImplementedError
