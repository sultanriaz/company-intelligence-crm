from typing import Optional
import httpx
from app.core.config import settings
from app.email.providers.base import BaseEmailProvider, ProviderSendResult


class ResendEmailProvider(BaseEmailProvider):
    name: str = "resend"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.RESEND_API_KEY

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
        if not self.api_key:
            return ProviderSendResult(
                success=False,
                provider_name="resend",
                status="FAILED",
                error_message="RESEND_API_KEY is not configured.",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        payload = {
            "from": f"{from_name} <{from_address}>",
            "to": [to_email],
            "subject": subject,
            "text": body_text,
            "html": body_html,
        }
        if reply_to:
            payload["reply_to"] = reply_to

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post("https://api.resend.com/emails", headers=headers, json=payload)
                if resp.status_code in {200, 201}:
                    data = resp.json()
                    return ProviderSendResult(
                        success=True,
                        provider_name="resend",
                        provider_message_id=data.get("id"),
                        status="SENT",
                        raw_response=data,
                    )
                else:
                    return ProviderSendResult(
                        success=False,
                        provider_name="resend",
                        status="FAILED",
                        error_message=f"HTTP {resp.status_code}: {resp.text}",
                    )
        except Exception as e:
            return ProviderSendResult(
                success=False,
                provider_name="resend",
                status="FAILED",
                error_message=str(e),
            )
