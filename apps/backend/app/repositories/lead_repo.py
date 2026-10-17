from typing import List, Optional
from sqlalchemy import select, and_, func, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import LeadScore, LeadScoreExplanation, CRMActivity
from app.models.pipeline import CRMPipeline, CRMStage
from app.models.company import Company
from app.repositories.base import BaseRepository


class LeadRepository(BaseRepository[LeadScore]):
    def __init__(self, session: AsyncSession):
        super().__init__(LeadScore, session)

    async def get_by_company(self, company_id: str) -> Optional[LeadScore]:
        query = (
            select(LeadScore)
            .where(LeadScore.company_id == company_id)
            .options(selectinload(LeadScore.explanations))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def upsert_score(
        self,
        company_id: str,
        total_score: int,
        industry_score: int,
        service_score: int,
        scale_score: int,
        opportunity_score: int,
        evidence_score: int,
        is_qualified: bool,
        qualification_notes: Optional[str] = None,
        explanations_data: Optional[List[dict]] = None,
    ) -> LeadScore:
        score = await self.get_by_company(company_id)
        if not score:
            score = LeadScore(company_id=company_id)
            self.session.add(score)

        score.total_score = total_score
        score.industry_score = industry_score
        score.service_score = service_score
        score.scale_score = scale_score
        score.opportunity_score = opportunity_score
        score.evidence_score = evidence_score
        score.is_qualified = is_qualified
        score.qualification_notes = qualification_notes

        await self.session.flush()

        if explanations_data:
            # Clear old explanations cleanly without accessing unpopulated relationship
            await self.session.execute(
                delete(LeadScoreExplanation).where(LeadScoreExplanation.lead_score_id == score.id)
            )

            for exp in explanations_data:
                explanation = LeadScoreExplanation(
                    lead_score_id=score.id,
                    dimension=exp.get("dimension", ""),
                    score_assigned=exp.get("score_assigned", 0),
                    max_score=exp.get("max_score", 25),
                    reason=exp.get("reason", ""),
                )
                self.session.add(explanation)
            await self.session.flush()

        return score

    async def list_pipelines(self, workspace_id: str) -> List[CRMPipeline]:
        query = (
            select(CRMPipeline)
            .where(CRMPipeline.workspace_id == workspace_id)
            .options(selectinload(CRMPipeline.stages))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_or_create_default_pipeline(self, workspace_id: str) -> CRMPipeline:
        query = (
            select(CRMPipeline)
            .where(and_(CRMPipeline.workspace_id == workspace_id, CRMPipeline.is_default == True))
            .options(selectinload(CRMPipeline.stages))
        )
        result = await self.session.execute(query)
        pipeline = result.scalars().first()
        if pipeline:
            return pipeline

        pipeline = CRMPipeline(
            workspace_id=workspace_id,
            name="Standard Sales Pipeline",
            is_default=True,
        )
        self.session.add(pipeline)
        await self.session.flush()

        default_stages = [
            ("Prospect Identified", 0, "#94a3b8"),
            ("Research Completed", 1, "#38bdf8"),
            ("Qualified Lead", 2, "#6366f1"),
            ("Outreach Staged", 3, "#a855f7"),
            ("Contacted / Awaiting Reply", 4, "#eab308"),
            ("Meeting Scheduled", 5, "#22c55e"),
            ("Unqualified", 6, "#ef4444"),
        ]
        for name, order_idx, color in default_stages:
            stage = CRMStage(
                pipeline_id=pipeline.id,
                name=name,
                order_index=order_idx,
                color=color,
            )
            self.session.add(stage)

        await self.session.flush()

        # Reload with eager loaded stages
        reload_query = (
            select(CRMPipeline)
            .where(CRMPipeline.id == pipeline.id)
            .options(selectinload(CRMPipeline.stages))
        )
        reloaded = await self.session.execute(reload_query)
        return reloaded.scalars().first()

    async def log_activity(
        self,
        workspace_id: str,
        company_id: str,
        activity_type: str,
        details: str,
        contact_id: Optional[str] = None,
        created_by: str = "SYSTEM",
    ) -> CRMActivity:
        activity = CRMActivity(
            workspace_id=workspace_id,
            company_id=company_id,
            contact_id=contact_id,
            activity_type=activity_type,
            details=details,
            created_by=created_by,
        )
        self.session.add(activity)
        await self.session.flush()
        return activity

    async def list_activities(
        self,
        workspace_id: str,
        company_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[CRMActivity]:
        filters = [CRMActivity.workspace_id == workspace_id]
        if company_id:
            filters.append(CRMActivity.company_id == company_id)

        query = (
            select(CRMActivity)
            .where(and_(*filters))
            .order_by(CRMActivity.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
