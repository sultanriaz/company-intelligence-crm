import pytest
from app.models.company import Company
from app.models.contact import Contact
from app.models.email import EmailDraft
from app.repositories.email_repo import EmailRepository


@pytest.mark.asyncio
async def test_email_outbox_and_double_send_prevention(async_client, db_session, seed_data, admin_token):
    workspace = seed_data["workspace"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Setup company and contact
    company = Company(
        workspace_id=workspace.id,
        name="Outreach Target Corp",
        primary_domain="target.example.com",
        status="QUALIFIED",
    )
    db_session.add(company)
    await db_session.flush()

    contact = Contact(
        workspace_id=workspace.id,
        company_id=company.id,
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@target.example.com",
        permission_status="LEGITIMATE_INTEREST",
    )
    db_session.add(contact)
    await db_session.flush()

    # 2. Create pending draft
    email_repo = EmailRepository(db_session)
    draft = await email_repo.create_draft(
        contact_id=contact.id,
        subject="Introductory Partnership",
        body_html="<p>Hello Jane</p>",
        body_text="Hello Jane",
    )
    await db_session.commit()

    # 3. Approve draft via API
    approval_payload = {
        "decision": "APPROVED",
        "feedback": "Approved by SDR lead.",
    }
    resp = await async_client.post(
        f"/api/v1/email/approvals/{draft.id}",
        json=approval_payload,
        headers=headers,
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["delivery_status"] in {"DRY_RUN", "SENT"}
    first_message_id = res_data["message_id"]
    assert first_message_id != ""

    # 4. Attempt double send (re-approval)
    # The transactional outbox must detect the existing idempotency key and prevent second delivery
    dup_resp = await async_client.post(
        f"/api/v1/email/approvals/{draft.id}",
        json=approval_payload,
        headers=headers,
    )
    assert dup_resp.status_code == 200
    dup_data = dup_resp.json()
    assert "Duplicate delivery prevented" in dup_data.get("error", "")
