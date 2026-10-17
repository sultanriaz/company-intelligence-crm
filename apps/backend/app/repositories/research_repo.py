import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.research import ResearchRun, AgentExecution, WorkflowCheckpoint
from app.repositories.base import BaseRepository


class ResearchRepository(BaseRepository[ResearchRun]):
    def __init__(self, session: AsyncSession):
        super().__init__(ResearchRun, session)

    async def get_run_with_details(self, workspace_id: str, run_id: str) -> Optional[ResearchRun]:
        query = (
            select(ResearchRun)
            .where(
                and_(
                    ResearchRun.workspace_id == workspace_id,
                    ResearchRun.id == run_id,
                )
            )
            .options(
                selectinload(ResearchRun.executions),
                selectinload(ResearchRun.checkpoints),
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_runs(
        self,
        workspace_id: str,
        company_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ResearchRun]:
        filters = [ResearchRun.workspace_id == workspace_id]
        if company_id:
            filters.append(ResearchRun.company_id == company_id)
        if status:
            filters.append(ResearchRun.status == status)

        query = (
            select(ResearchRun)
            .where(and_(*filters))
            .order_by(ResearchRun.created_at.desc())
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(ResearchRun.executions),
                selectinload(ResearchRun.checkpoints),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_runs(
        self,
        workspace_id: str,
        status: Optional[str] = None,
    ) -> int:
        filters = [ResearchRun.workspace_id == workspace_id]
        if status:
            filters.append(ResearchRun.status == status)
        query = select(func.count(ResearchRun.id)).where(and_(*filters))
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create_checkpoint(
        self,
        run_id: str,
        state: str,
        step_index: int,
        state_data: Dict[str, Any],
    ) -> WorkflowCheckpoint:
        checkpoint = WorkflowCheckpoint(
            research_run_id=run_id,
            state=state,
            step_index=step_index,
            state_data=json.dumps(state_data, default=str),
        )
        self.session.add(checkpoint)
        await self.session.flush()
        return checkpoint

    async def record_execution(
        self,
        run_id: str,
        agent_name: str,
        state: str,
        input_payload: Optional[Dict[str, Any]] = None,
        output_payload: Optional[Dict[str, Any]] = None,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        duration_ms: int = 0,
        error_message: Optional[str] = None,
    ) -> AgentExecution:
        execution = AgentExecution(
            research_run_id=run_id,
            agent_name=agent_name,
            state=state,
            input_payload=json.dumps(input_payload, default=str) if input_payload else None,
            output_payload=json.dumps(output_payload, default=str) if output_payload else None,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            error_message=error_message,
        )
        self.session.add(execution)
        await self.session.flush()
        return execution

    async def update_run_status(
        self,
        run_id: str,
        status: str,
        company_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[ResearchRun]:
        run = await self.get_by_id(run_id)
        if run:
            run.status = status
            if company_id:
                run.company_id = company_id
            if error_message:
                run.error_message = error_message
            if status in {"COMPLETED", "FAILED", "CANCELLED", "PARTIALLY_COMPLETED"}:
                run.completed_at = datetime.now(timezone.utc)
            await self.session.flush()
        return run
