import pytest
from app.email.compliance import compliance_service
from app.email.template_engine import render_email_template
from app.repositories.email_repo import EmailRepository


@pytest.mark.asyncio
async def test_email_compliance_suppression(db_session, seed_data):
    workspace = seed_data["workspace"]
    email_repo = EmailRepository(db_session)

    # Add suppressed email
    await email_repo.add_suppression(workspace.id, "unsubscribed@example.com", reason="UNSUBSCRIBE")
    await db_session.commit()

    eligibility = await compliance_service.check_eligibility(
        session=db_session,
        workspace_id=workspace.id,
        recipient_email="unsubscribed@example.com",
    )

    assert eligibility.is_eligible is False
    assert eligibility.is_suppressed is True
    assert "suppression list" in eligibility.rejection_reason


@pytest.mark.asyncio
async def test_email_compliance_approval_gate(db_session, seed_data):
    workspace = seed_data["workspace"]

    eligibility = await compliance_service.check_eligibility(
        session=db_session,
        workspace_id=workspace.id,
        recipient_email="lead@example.com",
        is_approved=False,
    )

    # By default, EMAIL_REQUIRE_APPROVAL=true, so unapproved draft is rejected
    assert eligibility.is_eligible is False
    assert "explicit human approval" in eligibility.rejection_reason


def test_render_email_template_with_footer():
    subject_tmpl = "Hello {{ name }} at {{ company }}"
    body_tmpl = "We noticed your product {{ product }}."
    context = {"name": "Bob", "company": "Acme", "product": "ETL Sync"}

    subj, text, html = render_email_template(subject_tmpl, body_tmpl, context)

    assert "Hello Bob at Acme" == subj
    assert "We noticed your product ETL Sync." in text
    assert "To unsubscribe from future communications" in text
    assert "<a href=" in html
    assert "Unsubscribe" in html
