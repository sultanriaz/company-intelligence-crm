import hashlib
import hmac
import json
import pytest
from app.core.config import settings
from app.repositories.email_repo import EmailRepository


@pytest.mark.asyncio
async def test_webhook_ingestion_and_auto_suppression(async_client, db_session, seed_data):
    workspace = seed_data["workspace"]
    secret = settings.EMAIL_WEBHOOK_SECRET

    # 1. Payload with bounce event
    bounce_payload = {
        "id": "evt-bounce-9999",
        "type": "bounce",
        "recipient": "bouncing.user@example.com",
    }
    raw_body = json.dumps(bounce_payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    headers = {
        "X-Webhook-Signature": sig,
        "Content-Type": "application/json",
    }

    # 2. Ingest webhook
    resp = await async_client.post("/api/v1/webhooks/email/resend", content=raw_body, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["processed"] is True

    # 3. Verify recipient was automatically added to suppression list
    email_repo = EmailRepository(db_session)
    is_supp = await email_repo.is_suppressed(workspace.id, "bouncing.user@example.com")
    assert is_supp is True

    # 4. Replay test: sending the same event ID should be recognized as duplicate
    replay_resp = await async_client.post("/api/v1/webhooks/email/resend", content=raw_body, headers=headers)
    assert replay_resp.status_code == 200
    assert replay_resp.json()["status"] == "received"
