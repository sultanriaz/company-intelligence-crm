import pytest
from pydantic import ValidationError
from app.schemas.contracts import (
    BusinessInsight,
    CompanyProfile,
    CRMSyncResult,
    DiscoveryResult,
    EmailDeliveryResult,
    EmailDraftResult,
    EmailEligibilityResult,
    LeadQualificationResult,
    ResearchFact,
    ResearchRequest,
    ScrapedPage,
    VerificationResult,
    WorkflowExecutionResult,
)


def test_research_request_validation():
    req = ResearchRequest(
        workspace_id="ws-123",
        target_url="https://example.com",
        crawl_depth=2,
        max_pages=20,
    )
    assert req.crawl_depth == 2

    with pytest.raises(ValidationError):
        ResearchRequest(workspace_id="ws-1", target_url="https://example.com", crawl_depth=10)


def test_research_fact_provenance():
    fact = ResearchFact(
        field="industry",
        value="Technology",
        source_url="https://example.com/about",
        confidence=0.95,
        verification_status="verified",
    )
    assert fact.confidence == 0.95
    assert fact.verification_status == "verified"


def test_lead_qualification_contract():
    res = LeadQualificationResult(
        company_name="Acme Corp",
        total_score=85,
        is_qualified=True,
        dimension_scores=[],
    )
    assert res.total_score == 85
    assert res.is_qualified is True
