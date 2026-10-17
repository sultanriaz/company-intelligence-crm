from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace_id
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.workspace import User
from app.orchestration.engine import orchestration_engine
from app.repositories.research_repo import ResearchRepository
from app.schemas.common import PaginatedResponse
from app.schemas.contracts import WorkflowExecutionResult
from app.schemas.research import ResearchRunCreate, ResearchRunResponse

router = APIRouter(prefix="/research", tags=["Multi-Agent Research"])


@router.post("/runs", response_model=WorkflowExecutionResult)
async def start_research_run(
    data: ResearchRunCreate,
    allow_local_for_testing: bool = Query(False),
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """
    Initiate autonomous multi-agent company intelligence workflow.
    Executes Discovery -> Scraping -> Research -> Verification -> Insights -> Qualification -> CRM Sync -> Email Prep.
    """
    result = await orchestration_engine.start_research_run(
        session=db,
        workspace_id=workspace_id,
        target_url=data.target_url,
        company_name=data.company_name,
        crawl_depth=data.crawl_depth,
        max_pages=data.max_pages,
        include_email_generation=data.include_email_generation,
        triggered_by="MANUAL",
        allow_local_for_testing=allow_local_for_testing,
    )
    await db.commit()
    return result


@router.get("/runs", response_model=PaginatedResponse[ResearchRunResponse])
async def list_research_runs(
    status: Optional[str] = None,
    company_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """List recent and active research runs."""
    repo = ResearchRepository(db)
    skip = (page - 1) * page_size
    items = await repo.list_runs(
        workspace_id=workspace_id,
        company_id=company_id,
        status=status,
        skip=skip,
        limit=page_size,
    )
    total = await repo.count_runs(workspace_id=workspace_id, status=status)

    return PaginatedResponse(
        items=[ResearchRunResponse.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 1,
    )


@router.get("/runs/{run_id}", response_model=ResearchRunResponse)
async def get_research_run(
    run_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """Inspect state, checkpoints, and agent executions for a research workflow."""
    repo = ResearchRepository(db)
    run = await repo.get_run_with_details(workspace_id, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found.")
    return run


@router.post("/runs/{run_id}/cancel")
async def cancel_research_run(
    run_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """Cancel an active research workflow."""
    repo = ResearchRepository(db)
    run = await repo.get_run_with_details(workspace_id, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found.")

    await repo.update_run_status(run.id, "CANCELLED", error_message="Cancelled by user.")
    await db.commit()
    return {"message": "Research run cancelled successfully", "run_id": run_id}
