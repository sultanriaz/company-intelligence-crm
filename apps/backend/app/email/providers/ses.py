from typing import Optional
from app.core.config import settings
from app.email.providers.base import BaseEmailProvider, ProviderSendResult
from app.email.providers.mock import MockEmailProvider
from app.email.providers.resend import ResendEmailProvider
from app.email.providers.sendgrid import SendGridEmailProvider


class SesEmailProvider(BaseEmailProvider):
    name: str = "ses"

    def __init__(
        self,
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None,
        region_name: Optional[str] = None,
    ):
        self.access_key = aws_access_key or settings.AWS_ACCESS_KEY_ID
        self.secret_key = aws_secret_key or settings.AWS_SECRET_ACCESS_KEY
        self.region = region_name or settings.AWS_REGION

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
        if not self.access_key or not self.secret_key:
            return ProviderSendResult(
                success=False,
                provider_name="ses",
                status="FAILED",
                error_message="AWS SES credentials not configured.",
            )

        try:
            import boto3
            client = boto3.client(
                "sesv2",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
            )
            response = client.send_email(
                FromEmailAddress=f"{from_name} <{from_address}>",
                Destination={"ToAddresses": [to_email]},
                Content={
                    "Simple": {
                        "Subject": {"Data": subject},
                        "Body": {
                            "Text": {"Data": body_text},
                            "Html": {"Data": body_html},
                        },
                    }
                },
            )
            return ProviderSendResult(
                success=True,
                provider_name="ses",
                provider_message_id=response.get("MessageId"),
                status="SENT",
                raw_response=response,
            )
        except Exception as e:
            return ProviderSendResult(
                success=False,
                provider_name="ses",
                status="FAILED",
                error_message=str(e),
            )


def get_email_provider() -> BaseEmailProvider:
    """Factory function returning the configured active email provider."""
    if settings.EMAIL_DRY_RUN:
        return MockEmailProvider()

    provider_name = settings.EMAIL_PROVIDER.lower()
    if provider_name == "resend":
        return ResendEmailProvider()
    elif provider_name == "sendgrid":
        return SendGridEmailProvider()
    elif provider_name == "ses":
        return SesEmailProvider()
    return MockEmailProvider()
