from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


def get_current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# 1. Research Request
class ResearchRequest(BaseModel):
    workspace_id: str
    target_url: str
    company_name: Optional[str] = None
    crawl_depth: int = Field(default=2, ge=1, le=5)
    max_pages: int = Field(default=15, ge=1, le=50)
    include_email_generation: bool = True
    trigger_source: str = "MANUAL"
    correlation_id: Optional[str] = None


# 2. Discovery Result
class DiscoveredPage(BaseModel):
    url: str
    category: str = "general"  # about, services, products, careers, contact, pricing, news
    priority: int = 1          # 1 (highest) to 5
    title: Optional[str] = None


class DiscoveryResult(BaseModel):
    domain: str
    seed_url: str
    total_discovered: int
    pages: List[DiscoveredPage] = Field(default_factory=list)
    discovery_metadata: Dict[str, str] = Field(default_factory=dict)


# 3. Scraped Page
class ScrapedPage(BaseModel):
    url: str
    http_status: int = 200
    title: str = ""
    meta_description: str = ""
    clean_text: str = ""
    content_hash: str = ""
    discovered_emails: List[str] = Field(default_factory=list)
    discovered_phones: List[str] = Field(default_factory=list)
    social_links: Dict[str, str] = Field(default_factory=dict)
    retrieved_at: str = Field(default_factory=get_current_utc_iso)
    is_rendered_js: bool = False


# 4. Research Fact
class ResearchFact(BaseModel):
    field: str
    value: str
    source_url: str
    retrieved_at: str = Field(default_factory=get_current_utc_iso)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    verification_status: str = "verified"  # verified, provisional, conflicted


# 5. Company Profile (Extracted and Consolidated)
class CompanyContactChannel(BaseModel):
    channel_type: str  # email, phone, linkedin, twitter, contact_form
    value: str
    source_url: str


class CompanyProfile(BaseModel):
    name: str
    legal_name: Optional[str] = None
    primary_domain: str
    industry: str = "Unknown"
    employee_range: str = "Unknown"
    description: str = ""
    headquarters: str = "Unknown"
    products_services: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    leadership: List[str] = Field(default_factory=list)
    contact_channels: List[CompanyContactChannel] = Field(default_factory=list)
    facts: List[ResearchFact] = Field(default_factory=list)


# 6. Verification Result
class VerificationResult(BaseModel):
    company_name: str
    domain: str
    verified_facts: List[ResearchFact]
    provisional_facts: List[ResearchFact] = Field(default_factory=list)
    conflicting_facts: List[ResearchFact] = Field(default_factory=list)
    overall_confidence_score: float = Field(default=0.9, ge=0.0, le=1.0)
    verification_notes: List[str] = Field(default_factory=list)


# 7. Business Insight
class OperationalHypothesis(BaseModel):
    challenge: str
    hypothesis_rationale: str
    needs_validation: bool = True


class BusinessInsight(BaseModel):
    company_name: str
    executive_summary: str
    target_market: str
    operational_challenges_hypotheses: List[OperationalHypothesis] = Field(default_factory=list)
    market_opportunities: List[str] = Field(default_factory=list)
    company_specific_value_proposition: str
    recommended_outreach_angle: str
    identified_research_gaps: List[str] = Field(default_factory=list)


# 8. Lead Qualification Result
class DimensionScore(BaseModel):
    dimension_name: str
    score: int
    max_score: int
    rationale: str


class LeadQualificationResult(BaseModel):
    company_name: str
    total_score: int = Field(ge=0, le=100)
    is_qualified: bool
    threshold: int = 60
    dimension_scores: List[DimensionScore] = Field(default_factory=list)
    recommended_pipeline_stage: str = "Qualified Lead"


# 9. CRM Sync Result
class CRMSyncResult(BaseModel):
    company_id: str
    primary_domain: str
    contacts_synced_count: int
    facts_synced_count: int
    status: str
    pipeline_stage: str
    synced_at: str = Field(default_factory=get_current_utc_iso)


# 10. Email Draft Result
class EmailDraftResult(BaseModel):
    subject: str
    body_text: str
    body_html: str
    recipient_email: str
    recipient_name: str
    referenced_fact_fields: List[str] = Field(default_factory=list)
    value_proposition_used: str
    tone: str = "professional"
    draft_status: str = "PENDING_APPROVAL"


# 11. Email Eligibility Result
class EmailEligibilityResult(BaseModel):
    recipient_email: str
    is_eligible: bool
    rejection_reason: Optional[str] = None
    lawful_basis: str = "LEGITIMATE_INTEREST"
    is_suppressed: bool = False
    rate_limit_passed: bool = True


# 12. Email Delivery Result
class EmailDeliveryResult(BaseModel):
    message_id: str
    idempotency_key: str
    provider: str
    provider_message_id: Optional[str] = None
    delivery_status: str  # SENT, DRY_RUN, REJECTED, FAILED
    dispatched_at: str = Field(default_factory=get_current_utc_iso)
    error: Optional[str] = None


# 13. Workflow Execution Result
class WorkflowExecutionResult(BaseModel):
    run_id: str
    status: str
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    steps_completed: List[str] = Field(default_factory=list)
    lead_score: Optional[int] = None
    is_qualified: bool = False
    email_draft_id: Optional[str] = None
    email_approval_status: Optional[str] = None
    total_duration_ms: int = 0
    total_cost_usd: float = 0.0
    errors: List[str] = Field(default_factory=list)
