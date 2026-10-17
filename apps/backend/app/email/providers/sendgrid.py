from typing import Optional
import httpx
from app.core.config import settings
from app.email.providers.base import BaseEmailProvider, ProviderSendResult


class SendGridEmailProvider(BaseEmailProvider):
    name: str = "sendgrid"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SENDGRID_API_KEY

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
                provider_name="sendgrid",
                status="FAILED",
                error_message="SENDGRID_API_KEY is not configured.",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": from_address, "name": from_name},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": body_text},
                {"type": "text/html", "value": body_html},
            ],
        }
        if reply_to:
            payload["reply_to"] = {"email": reply_to}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post("https://api.sendgrid.com/v3/mail/send", headers=headers, json=payload)
                if resp.status_code in {200, 202}:
                    msg_id = resp.headers.get("X-Message-Id") or f"sg-{idempotency_key}"
                    return ProviderSendResult(
                        success=True,
                        provider_name="sendgrid",
                        provider_message_id=msg_id,
                        status="SENT",
                    )
                else:
                    return ProviderSendResult(
                        success=False,
                        provider_name="sendgrid",
                        status="FAILED",
                        error_message=f"HTTP {resp.status_code}: {resp.text}",
                    )
        except Exception as e:
            return ProviderSendResult(
                success=False,
                provider_name="sendgrid",
                status="FAILED",
                error_message=str(e),
            )
