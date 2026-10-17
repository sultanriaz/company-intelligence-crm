from typing import List, Optional
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company, CompanyDomain, CompanySource, ResearchFact, ResearchReport
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, session: AsyncSession):
        super().__init__(Company, session)

    async def get_by_domain(self, workspace_id: str, domain: str) -> Optional[Company]:
        normalized_domain = domain.strip().lower()
        query = (
            select(Company)
            .where(
                and_(
                    Company.workspace_id == workspace_id,
                    Company.primary_domain == normalized_domain,
                )
            )
            .options(
                selectinload(Company.facts),
                selectinload(Company.reports),
                selectinload(Company.lead_score),
                selectinload(Company.contacts),
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_with_details(self, workspace_id: str, company_id: str) -> Optional[Company]:
        query = (
            select(Company)
            .where(
                and_(
                    Company.workspace_id == workspace_id,
                    Company.id == company_id,
                )
            )
            .options(
                selectinload(Company.facts),
                selectinload(Company.reports),
                selectinload(Company.lead_score),
                selectinload(Company.contacts),
                selectinload(Company.domains),
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_companies(
        self,
        workspace_id: str,
        status: Optional[str] = None,
        industry: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Company]:
        filters = [Company.workspace_id == workspace_id]
        if status:
            filters.append(Company.status == status)
        if industry:
            filters.append(Company.industry == industry)
        if search:
            search_term = f"%{search}%"
            filters.append(
                or_(
                    Company.name.ilike(search_term),
                    Company.primary_domain.ilike(search_term),
                    Company.description.ilike(search_term),
                )
            )

        query = (
            select(Company)
            .where(and_(*filters))
            .order_by(Company.created_at.desc())
            .offset(skip)
            .limit(limit)
            .options(selectinload(Company.lead_score))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_companies(
        self,
        workspace_id: str,
        status: Optional[str] = None,
        industry: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        filters = [Company.workspace_id == workspace_id]
        if status:
            filters.append(Company.status == status)
        if industry:
            filters.append(Company.industry == industry)
        if search:
            search_term = f"%{search}%"
            filters.append(
                or_(
                    Company.name.ilike(search_term),
                    Company.primary_domain.ilike(search_term),
                )
            )

        query = select(func.count(Company.id)).where(and_(*filters))
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def upsert_company(
        self,
        workspace_id: str,
        name: str,
        primary_domain: str,
        description: Optional[str] = None,
        industry: Optional[str] = None,
        employee_range: Optional[str] = None,
        headquarters: Optional[str] = None,
        legal_name: Optional[str] = None,
    ) -> Company:
        normalized_domain = primary_domain.strip().lower()
        existing = await self.get_by_domain(workspace_id, normalized_domain)
        if existing:
            if name and existing.name == "Unknown":
                existing.name = name
            if description and not existing.description:
                existing.description = description
            if industry and not existing.industry:
                existing.industry = industry
            if employee_range and not existing.employee_range:
                existing.employee_range = employee_range
            if headquarters and not existing.headquarters:
                existing.headquarters = headquarters
            if legal_name and not existing.legal_name:
                existing.legal_name = legal_name
            await self.session.flush()
            return existing

        company = Company(
            workspace_id=workspace_id,
            name=name or normalized_domain,
            primary_domain=normalized_domain,
            description=description,
            industry=industry,
            employee_range=employee_range,
            headquarters=headquarters,
            legal_name=legal_name,
            status="PROSPECT",
        )
        self.session.add(company)
        await self.session.flush()

        # Add primary domain entry
        domain_entry = CompanyDomain(
            company_id=company.id,
            domain=normalized_domain,
            is_primary=True,
        )
        self.session.add(domain_entry)
        await self.session.flush()

        return company

    async def add_fact(
        self,
        company_id: str,
        field_name: str,
        field_value: str,
        source_url: str,
        confidence_score: float = 1.0,
        verification_status: str = "VERIFIED",
        run_id: Optional[str] = None,
    ) -> ResearchFact:
        fact = ResearchFact(
            company_id=company_id,
            run_id=run_id,
            field_name=field_name,
            field_value=field_value,
            source_url=source_url,
            confidence_score=confidence_score,
            verification_status=verification_status,
        )
        self.session.add(fact)
        await self.session.flush()
        return fact

    async def add_source(
        self,
        company_id: str,
        url: str,
        http_status: int,
        content_hash: str,
        raw_text: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> CompanySource:
        source = CompanySource(
            company_id=company_id,
            run_id=run_id,
            url=url,
            http_status=http_status,
            content_hash=content_hash,
            raw_text=raw_text,
        )
        self.session.add(source)
        await self.session.flush()
        return source

    async def add_report(
        self,
        company_id: str,
        executive_summary: str,
        challenges_hypotheses: Optional[str] = None,
        opportunities: Optional[str] = None,
        tech_stack: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> ResearchReport:
        report = ResearchReport(
            company_id=company_id,
            run_id=run_id,
            executive_summary=executive_summary,
            challenges_hypotheses=challenges_hypotheses,
            opportunities=opportunities,
            tech_stack=tech_stack,
        )
        self.session.add(report)
        await self.session.flush()
        return report
