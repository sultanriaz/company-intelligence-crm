import asyncio
import os
import sys

# Ensure backend app in pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend")))

from app.core.database import AsyncSessionLocal, init_db
from app.core.security import get_password_hash
from app.models.workspace import User, Workspace
from app.models.company import Company, CompanyDomain, ResearchFact, ResearchReport
from app.models.contact import Contact
from app.models.lead import LeadScore, LeadScoreExplanation, CRMActivity
from app.models.campaign import EmailTemplate, EmailCampaign
from app.repositories.lead_repo import LeadRepository


async def seed():
    print("Initializing database tables...")
    await init_db()

    async with AsyncSessionLocal() as session:
        print("Seeding workspace and admin user...")
        # 1. Create Workspace
        workspace = Workspace(name="Acme Enterprise Corp", slug="acme-enterprise")
        session.add(workspace)
        await session.flush()

        # 2. Create Admin User
        admin_user = User(
            workspace_id=workspace.id,
            email="admin@company-intelligence.local",
            password_hash=get_password_hash("AdminPass123!"),
            full_name="Sarah Connor",
            role="ADMIN",
            is_active=True,
        )
        session.add(admin_user)
        await session.flush()

        # 3. Pipeline
        lead_repo = LeadRepository(session)
        pipeline = await lead_repo.get_or_create_default_pipeline(workspace.id)

        # 4. Email Template
        template = EmailTemplate(
            workspace_id=workspace.id,
            name="Executive Value Proposition",
            subject_template="Scaling {{ company_name }}'s Data Pipelines with Automated AI",
            body_template=(
                "Hi {{ contact_name }},\n\n"
                "I have been following {{ company_name }}'s growth in {{ industry }}. "
                "Many engineering teams scaling distributed workflows face significant operational overhead maintaining multi-cloud data sync.\n\n"
                "We help companies like yours streamline pipeline observability, reducing maintenance overhead by up to 40%.\n\n"
                "Would you be open to a 10-minute introductory call next Tuesday?\n\n"
                "Best regards,\n"
                "{{ sender_name }}"
            ),
        )
        session.add(template)

        # 5. Campaign
        campaign = EmailCampaign(
            workspace_id=workspace.id,
            name="Q4 Enterprise Outreach",
            status="ACTIVE",
            auto_send_enabled=False,
            daily_limit=50,
        )
        session.add(campaign)
        await session.flush()

        # 6. Sample Company 1: Acme Innovations
        company1 = Company(
            workspace_id=workspace.id,
            name="Acme Innovations Inc",
            primary_domain="acme.example.com",
            industry="Enterprise Software & Cloud AI",
            employee_range="50-200",
            description="Acme Innovations builds automated data integration and machine learning pipelines for B2B enterprises.",
            headquarters="San Francisco, CA, USA",
            status="QUALIFIED",
            pipeline_stage_id=pipeline.stages[2].id,  # Qualified Lead
        )
        session.add(company1)
        await session.flush()

        c1_domain = CompanyDomain(company_id=company1.id, domain="acme.example.com", is_primary=True)
        session.add(c1_domain)

        # Contact 1
        contact1 = Contact(
            workspace_id=workspace.id,
            company_id=company1.id,
            first_name="Alice",
            last_name="Vance",
            email="alice@acme.example.com",
            title="Chief Executive Officer",
            phone="+1-415-555-0199",
            provenance_url="https://acme.example.com/team",
            permission_status="LEGITIMATE_INTEREST",
        )
        session.add(contact1)

        # Facts for Company 1
        f1 = ResearchFact(
            company_id=company1.id,
            field_name="industry",
            field_value="Enterprise Software & Cloud AI",
            source_url="https://acme.example.com/about",
            confidence_score=0.98,
            verification_status="VERIFIED",
        )
        f2 = ResearchFact(
            company_id=company1.id,
            field_name="products",
            field_value="Cloud Data Pipeline Platform, Automated ETL Sync",
            source_url="https://acme.example.com/products",
            confidence_score=0.95,
            verification_status="VERIFIED",
        )
        session.add_all([f1, f2])

        # Report for Company 1
        rep1 = ResearchReport(
            company_id=company1.id,
            executive_summary="Acme Innovations is a recognized cloud data platform provider focusing on automated ETL pipelines.",
            challenges_hypotheses='[{"challenge": "Scaling distributed data transformations across heterogeneous multi-cloud environments.", "hypothesis_rationale": "High customer volume and custom on-prem connector demands.", "needs_validation": true}]',
            opportunities='["Expansion into automated AI-driven ETL monitoring.", "Modernizing legacy database migrations for financial services clients."]',
            tech_stack='["Python", "FastAPI", "React", "PostgreSQL", "Docker", "AWS"]',
        )
        session.add(rep1)

        # Score for Company 1
        score1 = LeadScore(
            company_id=company1.id,
            total_score=88,
            industry_score=25,
            service_score=25,
            scale_score=20,
            opportunity_score=12,
            evidence_score=6,
            is_qualified=True,
            qualification_notes="High-value target with confirmed commercial scale and strong service alignment.",
        )
        session.add(score1)
        await session.flush()

        exp1_1 = LeadScoreExplanation(
            lead_score_id=score1.id,
            dimension="industry_relevance",
            score_assigned=25,
            max_score=25,
            reason="Core target industry (Enterprise Cloud AI)",
        )
        exp1_2 = LeadScoreExplanation(
            lead_score_id=score1.id,
            dimension="service_compatibility",
            score_assigned=25,
            max_score=25,
            reason="Demonstrated requirement for automated ETL & pipeline monitoring",
        )
        session.add_all([exp1_1, exp1_2])

        # Activity for Company 1
        act1 = CRMActivity(
            workspace_id=workspace.id,
            company_id=company1.id,
            contact_id=contact1.id,
            activity_type="RESEARCH_DONE",
            details="Initial multi-agent intelligence gathered. Lead qualified with score 88/100.",
            created_by="MULTI_AGENT_SUPERVISOR",
        )
        session.add(act1)

        # Sample Company 2: Beta Logistics
        company2 = Company(
            workspace_id=workspace.id,
            name="Beta Global Logistics",
            primary_domain="betalogistics.example.com",
            industry="Transportation & Supply Chain",
            employee_range="10-50",
            description="Regional freight forwarder and warehouse logistics provider.",
            headquarters="Chicago, IL, USA",
            status="PROSPECT",
            pipeline_stage_id=pipeline.stages[0].id,  # Prospect Identified
        )
        session.add(company2)
        await session.flush()

        c2_domain = CompanyDomain(company_id=company2.id, domain="betalogistics.example.com", is_primary=True)
        session.add(c2_domain)

        score2 = LeadScore(
            company_id=company2.id,
            total_score=42,
            industry_score=15,
            service_score=8,
            scale_score=14,
            opportunity_score=5,
            evidence_score=0,
            is_qualified=False,
            qualification_notes="Secondary industry fit. Low technology signal density in public filings.",
        )
        session.add(score2)

        await session.commit()
        print("Demo database successfully seeded!")
        print("Credentials: admin@company-intelligence.local / AdminPass123!")


if __name__ == "__main__":
    asyncio.run(seed())
