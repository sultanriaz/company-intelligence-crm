import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.repositories.company_repo import CompanyRepository
from app.repositories.contact_repo import ContactRepository
from app.repositories.lead_repo import LeadRepository
from app.schemas.contracts import BusinessInsight, CompanyProfile, CRMSyncResult, LeadQualificationResult, VerificationResult


class CRMIntegrationAgent(BaseAgent):
    """
    Agent 8: CRM Integration Agent.
    Deterministically synchronizes company, contact, research facts,
    reports, and lead score records into the PostgreSQL database.
    """

    def __init__(self):
        super().__init__(name="CRMIntegrationAgent")

    async def execute_task(
        self,
        session: AsyncSession,
        workspace_id: str,
        profile: CompanyProfile,
        verification: VerificationResult,
        insights: BusinessInsight,
        lead_score: LeadQualificationResult,
        run_id: Optional[str] = None,
    ) -> CRMSyncResult:
        company_repo = CompanyRepository(session)
        contact_repo = ContactRepository(session)
        lead_repo = LeadRepository(session)

        # 1. Upsert company record
        company = await company_repo.upsert_company(
            workspace_id=workspace_id,
            name=profile.name,
            primary_domain=profile.primary_domain,
            description=profile.description,
            industry=profile.industry,
            employee_range=profile.employee_range,
            headquarters=profile.headquarters,
            legal_name=profile.legal_name,
        )

        # Update company status if qualified
        company.status = "QUALIFIED" if lead_score.is_qualified else "PROSPECT"

        # 2. Persist verified and provisional facts
        facts_synced = 0
        all_facts = verification.verified_facts + verification.provisional_facts
        for fact in all_facts:
            await company_repo.add_fact(
                company_id=company.id,
                field_name=fact.field,
                field_value=fact.value,
                source_url=fact.source_url,
                confidence_score=fact.confidence,
                verification_status=fact.verification_status,
                run_id=run_id,
            )
            facts_synced += 1

        # 3. Persist research report
        challenges_json = json.dumps([c.model_dump() for c in insights.operational_challenges_hypotheses])
        opportunities_json = json.dumps(insights.market_opportunities)
        tech_json = json.dumps(profile.technologies)

        await company_repo.add_report(
            company_id=company.id,
            executive_summary=insights.executive_summary,
            challenges_hypotheses=challenges_json,
            opportunities=opportunities_json,
            tech_stack=tech_json,
            run_id=run_id,
        )

        # 4. Upsert lead qualification score
        explanations_data = [
            {
                "dimension": d.dimension_name,
                "score_assigned": d.score,
                "max_score": d.max_score,
                "reason": d.rationale,
            }
            for d in lead_score.dimension_scores
        ]
        await lead_repo.upsert_score(
            company_id=company.id,
            total_score=lead_score.total_score,
            industry_score=next((d.score for d in lead_score.dimension_scores if d.dimension_name == "industry_relevance"), 0),
            service_score=next((d.score for d in lead_score.dimension_scores if d.dimension_name == "service_compatibility"), 0),
            scale_score=next((d.score for d in lead_score.dimension_scores if d.dimension_name == "company_characteristics"), 0),
            opportunity_score=next((d.score for d in lead_score.dimension_scores if d.dimension_name == "opportunity_signals"), 0),
            evidence_score=next((d.score for d in lead_score.dimension_scores if d.dimension_name == "evidence_quality"), 0),
            is_qualified=lead_score.is_qualified,
            qualification_notes=f"Scored {lead_score.total_score}/100. Target pipeline: {lead_score.recommended_pipeline_stage}",
            explanations_data=explanations_data,
        )

        # 5. Upsert discovered contacts
        contacts_synced = 0
        for ch in profile.contact_channels:
            if ch.channel_type == "email":
                # Create contact
                first_name = "Team"
                last_name = ""
                # If leadership available, associate with top leader
                if profile.leadership:
                    first_leader = profile.leadership[0].split("(")[0].strip()
                    parts = first_leader.split()
                    if len(parts) >= 1:
                        first_name = parts[0]
                    if len(parts) >= 2:
                        last_name = " ".join(parts[1:])

                await contact_repo.upsert_contact(
                    workspace_id=workspace_id,
                    company_id=company.id,
                    email=ch.value,
                    first_name=first_name,
                    last_name=last_name,
                    provenance_url=ch.source_url,
                    permission_status="LEGITIMATE_INTEREST",
                )
                contacts_synced += 1

        # 6. Log CRM activity
        await lead_repo.log_activity(
            workspace_id=workspace_id,
            company_id=company.id,
            activity_type="RESEARCH_DONE",
            details=f"Automated multi-agent research completed. Score: {lead_score.total_score}/100. Facts: {facts_synced}.",
            created_by="MULTI_AGENT_SUPERVISOR",
        )

        return CRMSyncResult(
            company_id=company.id,
            primary_domain=company.primary_domain,
            contacts_synced_count=contacts_synced,
            facts_synced_count=facts_synced,
            status=company.status,
            pipeline_stage=lead_score.recommended_pipeline_stage,
        )


crm_sync_agent = CRMIntegrationAgent()
