import os
import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.models.company import Company
from app.models.email import EmailDraft
from app.models.research import ResearchRun
from app.orchestration.engine import orchestration_engine
from app.repositories.company_repo import CompanyRepository
from app.repositories.email_repo import EmailRepository


def load_fixture_html() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_site.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.mark.asyncio
async def test_end_to_end_acceptance_scenario(db_session, seed_data):
    """
    End-to-End Full Acceptance Scenario:
    Executes the 11-agent coordination from initial URL submission,
    crawling, research extraction, fact verification with citations,
    lead qualification, CRM record persistence, email drafting,
    and approved outbox delivery.
    """
    workspace = seed_data["workspace"]
    html_content = load_fixture_html()

    # Mock scraper HTTP responses with local HTML fixture
    mock_response = httpx.Response(
        status_code=200,
        text=html_content,
        headers={"content-type": "text/html"},
        request=httpx.Request("GET", "https://acme.example.com"),
    )

    with patch("app.scraping.client.scraper_client.fetch_page", new=AsyncMock(return_value=mock_response)):
        # 1. User submits company website to start autonomous research
        workflow_result = await orchestration_engine.start_research_run(
            session=db_session,
            workspace_id=workspace.id,
            target_url="https://acme.example.com",
            company_name="Acme Innovations",
            crawl_depth=2,
            max_pages=5,
            include_email_generation=True,
            allow_local_for_testing=True,
        )

        assert workflow_result.status == "COMPLETED"
        assert workflow_result.company_id is not None
        assert workflow_result.lead_score >= 60
        assert workflow_result.is_qualified is True
        assert workflow_result.email_draft_id is not None
        assert len(workflow_result.steps_completed) >= 8

        # 2. Verify Company record in CRM database
        company_repo = CompanyRepository(db_session)
        company = await company_repo.get_with_details(workspace.id, workflow_result.company_id)
        assert company is not None
        assert company.name == "Acme Innovations Inc"
        assert company.primary_domain == "acme.example.com"
        assert len(company.facts) > 0
        assert len(company.reports) > 0

        # Verify fact citations
        assert all(f.source_url.startswith("http") for f in company.facts)
        assert all(f.confidence_score >= 0.8 for f in company.facts)

        # 3. Verify Generated Email Draft
        email_repo = EmailRepository(db_session)
        draft = await email_repo.get_draft(workflow_result.email_draft_id)
        assert draft is not None
        assert draft.status == "PENDING_APPROVAL"
        assert "Acme" in draft.subject
        assert "Unsubscribe" in draft.body_text

        # 4. Human Approval Gate & Outbox Delivery
        from app.email.outbox import outbox_service
        delivery_res = await outbox_service.stage_and_dispatch(
            session=db_session,
            workspace_id=workspace.id,
            draft=draft,
            is_approved=True,
        )

        assert delivery_res.delivery_status in {"DRY_RUN", "SENT"}
        assert delivery_res.idempotency_key != ""
        assert delivery_res.message_id != ""

        # 5. Verify Draft is updated to SENT
        await db_session.refresh(draft)
        assert draft.status == "SENT"
