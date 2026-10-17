from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace_id
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.research import AgentExecution, ResearchRun
from app.models.workspace import User
from app.schemas.research import AgentExecutionResponse

router = APIRouter(prefix="/agents", tags=["Agent Performance & Telemetry"])


@router.get("/executions", response_model=List[AgentExecutionResponse])
async def list_agent_executions(
    agent_name: Optional[str] = None,
    run_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """Inspect individual agent execution traces, durations, token counts, and cost telemetry."""
    query = (
        select(AgentExecution)
        .join(ResearchRun, AgentExecution.research_run_id == ResearchRun.id)
        .where(ResearchRun.workspace_id == workspace_id)
        .order_by(AgentExecution.created_at.desc())
        .limit(limit)
    )
    if agent_name:
        query = query.where(AgentExecution.agent_name == agent_name)
    if run_id:
        query = query.where(AgentExecution.research_run_id == run_id)

    result = await db.execute(query)
    return list(result.scalars().all())
