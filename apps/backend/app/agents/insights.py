from app.agents.base import BaseAgent
from app.agents.llm import get_llm_adapter
from app.schemas.contracts import BusinessInsight, CompanyProfile, VerificationResult


class BusinessInsightsAgent(BaseAgent):
    """
    Agent 6: Business Insights Agent.
    Derives company-specific value propositions, market opportunities,
    and operational challenges (explicitly labeled as testable hypotheses).
    """

    def __init__(self):
        super().__init__(name="BusinessInsightsAgent")

    async def execute_task(
        self,
        profile: CompanyProfile,
        verification: VerificationResult,
    ) -> BusinessInsight:
        system_instruction = (
            "You are a Senior Strategic B2B Consultant and Commercial Advisor. "
            "Analyze verified company intelligence and synthesize business summaries, "
            "value propositions, and operational hypotheses. "
            "IMPORTANT: All operational challenges must be framed as testable hypotheses requiring validation."
        )

        prompt = (
            f"Generate business insights for '{profile.name}' ({profile.primary_domain}).\n"
            f"Industry: {profile.industry}\n"
            f"Description: {profile.description}\n"
            f"Products/Services: {', '.join(profile.products_services)}\n"
            f"Technologies: {', '.join(profile.technologies)}\n"
            f"Verified Facts count: {len(verification.verified_facts)}\n\n"
            "Return a BusinessInsight JSON object containing:\n"
            "- executive_summary\n"
            "- target_market\n"
            "- operational_challenges_hypotheses (list with challenge, hypothesis_rationale, needs_validation=true)\n"
            "- market_opportunities\n"
            "- company_specific_value_proposition\n"
            "- recommended_outreach_angle\n"
            "- identified_research_gaps"
        )

        llm = get_llm_adapter()
        insights = await llm.generate_structured(prompt, system_instruction, BusinessInsight)
        insights.company_name = profile.name
        return insights


insights_agent = BusinessInsightsAgent()
