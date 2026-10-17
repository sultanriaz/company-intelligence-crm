import pytest
from app.agents.qualification import qualification_agent
from app.schemas.contracts import BusinessInsight, CompanyProfile, OperationalHypothesis, ResearchFact, VerificationResult


@pytest.mark.asyncio
async def test_qualification_scoring_high_fit():
    profile = CompanyProfile(
        name="TechCorp",
        primary_domain="techcorp.com",
        industry="Enterprise Software & Cloud AI",
        employee_range="50-200",
        description="B2B software solutions.",
        products_services=["ETL Pipeline", "Data Lake Sync", "ML Engine"],
        technologies=["Python", "PostgreSQL"],
    )

    insights = BusinessInsight(
        company_name="TechCorp",
        executive_summary="Summary",
        target_market="Enterprise",
        operational_challenges_hypotheses=[
            OperationalHypothesis(challenge="Data sync latency", hypothesis_rationale="Scaling fast")
        ],
        market_opportunities=["Cloud migration", "AI monitoring"],
        company_specific_value_proposition="Reduces sync latency by 50%",
        recommended_outreach_angle="Real-time monitoring",
    )

    verification = VerificationResult(
        company_name="TechCorp",
        domain="techcorp.com",
        verified_facts=[
            ResearchFact(field="industry", value="Software", source_url="https://techcorp.com", confidence=0.95)
        ],
        overall_confidence_score=0.95,
    )

    result = await qualification_agent.execute_task(profile, insights, verification)

    assert result.total_score >= 80
    assert result.is_qualified is True
    assert len(result.dimension_scores) == 5


@pytest.mark.asyncio
async def test_qualification_scoring_low_fit():
    profile = CompanyProfile(
        name="Local Bakery",
        primary_domain="bakery.local",
        industry="Food & Beverages",
        employee_range="1-5",
        description="Fresh pastries daily.",
        products_services=["Bread"],
    )

    insights = BusinessInsight(
        company_name="Local Bakery",
        executive_summary="Bakery",
        target_market="Local retail",
        operational_challenges_hypotheses=[],
        market_opportunities=[],
        company_specific_value_proposition="Fresh bread",
        recommended_outreach_angle="Bakery supplies",
    )

    verification = VerificationResult(
        company_name="Local Bakery",
        domain="bakery.local",
        verified_facts=[],
        overall_confidence_score=0.5,
    )

    result = await qualification_agent.execute_task(profile, insights, verification)

    assert result.total_score < 60
    assert result.is_qualified is False
