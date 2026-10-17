from typing import Optional
from app.agents.base import BaseAgent
from app.agents.llm import get_llm_adapter
from app.schemas.contracts import BusinessInsight, CompanyProfile, EmailDraftResult, VerificationResult


class PersonalizedEmailAgent(BaseAgent):
    """
    Agent 9: Personalized Email Agent.
    Drafts tailored, evidence-backed B2B outreach communications.
    Strictly forbids false familiarity or unsubstantiated claims.
    """

    def __init__(self):
        super().__init__(name="PersonalizedEmailAgent")

    async def execute_task(
        self,
        profile: CompanyProfile,
        insights: BusinessInsight,
        verification: VerificationResult,
        recipient_name: Optional[str] = None,
        recipient_email: Optional[str] = None,
    ) -> EmailDraftResult:
        contact_name = recipient_name or (profile.leadership[0].split("(")[0].strip() if profile.leadership else "Team")
        target_email = recipient_email or (profile.contact_channels[0].value if profile.contact_channels else f"contact@{profile.primary_domain}")

        verified_fields = [f.field for f in verification.verified_facts]

        system_instruction = (
            "You are a professional B2B Sales Development Director. "
            "Write a concise, respectful, value-focused cold email draft based ONLY on verified company facts. "
            "DO NOT claim prior conversations, shared acquaintances, or personal familiarity. "
            "Focus on the company's verified value proposition and operational challenges."
        )

        prompt = (
            f"Draft an outreach email to '{contact_name}' at '{profile.name}' ({profile.primary_domain}).\n"
            f"Target Email: {target_email}\n"
            f"Industry: {profile.industry}\n"
            f"Value Proposition: {insights.company_specific_value_proposition}\n"
            f"Recommended Angle: {insights.recommended_outreach_angle}\n"
            f"Verified Facts: {', '.join(verified_fields)}\n\n"
            "Return an EmailDraftResult JSON object containing:\n"
            "- subject\n"
            "- body_text (plain text version with greeting, value proposition, call to action, and unsubscribe line)\n"
            "- body_html (clean HTML version with unsubscribe link)\n"
            "- recipient_email\n"
            "- recipient_name\n"
            "- referenced_fact_fields (list of referenced fact names)\n"
            "- value_proposition_used\n"
            "- tone: 'professional'\n"
            "- draft_status: 'PENDING_APPROVAL'"
        )

        llm = get_llm_adapter()
        draft = await llm.generate_structured(prompt, system_instruction, EmailDraftResult)
        draft.recipient_email = target_email
        draft.recipient_name = contact_name
        return draft


email_draft_agent = PersonalizedEmailAgent()
