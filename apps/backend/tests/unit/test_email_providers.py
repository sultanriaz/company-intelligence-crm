import pytest
from app.email.providers import (
    MockEmailProvider,
    ResendEmailProvider,
    SendGridEmailProvider,
    SesEmailProvider,
    get_email_provider,
)


@pytest.mark.asyncio
async def test_mock_email_provider():
    provider = MockEmailProvider()
    res = await provider.send_email(
        to_email="test@example.com",
        subject="Test Subject",
        body_text="Plain text body",
        body_html="<p>Html body</p>",
        from_address="outreach@local",
        from_name="Outreach",
        idempotency_key="key-123",
    )
    assert res.success is True
    assert res.provider_name == "mock"
    assert res.status == "DRY_RUN"
    assert res.provider_message_id is not None


@pytest.mark.asyncio
async def test_resend_missing_api_key():
    provider = ResendEmailProvider(api_key=None)
    res = await provider.send_email(
        to_email="test@example.com",
        subject="Test",
        body_text="Test",
        body_html="<p>Test</p>",
        from_address="outreach@local",
        from_name="Outreach",
    )
    assert res.success is False
    assert "RESEND_API_KEY is not configured" in res.error_message


@pytest.mark.asyncio
async def test_sendgrid_missing_api_key():
    provider = SendGridEmailProvider(api_key=None)
    res = await provider.send_email(
        to_email="test@example.com",
        subject="Test",
        body_text="Test",
        body_html="<p>Test</p>",
        from_address="outreach@local",
        from_name="Outreach",
    )
    assert res.success is False
    assert "SENDGRID_API_KEY is not configured" in res.error_message


@pytest.mark.asyncio
async def test_ses_missing_credentials():
    provider = SesEmailProvider(aws_access_key=None, aws_secret_key=None)
    res = await provider.send_email(
        to_email="test@example.com",
        subject="Test",
        body_text="Test",
        body_html="<p>Test</p>",
        from_address="outreach@local",
        from_name="Outreach",
    )
    assert res.success is False
    assert "AWS SES credentials not configured" in res.error_message


def test_get_email_provider_factory():
    provider = get_email_provider()
    # When EMAIL_DRY_RUN=true, default is MockEmailProvider
    assert isinstance(provider, MockEmailProvider)
