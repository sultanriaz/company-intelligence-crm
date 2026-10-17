from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace_id
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.company import Company
from app.models.lead import LeadScore
from app.models.workspace import User
from app.repositories.lead_repo import LeadRepository
from app.schemas.lead import LeadScoreOverride, LeadScoreResponse

router = APIRouter(prefix="/leads", tags=["Lead Scoring & Qualification"])


@router.get("", response_model=List[LeadScoreResponse])
async def list_leads(
    is_qualified: Optional[bool] = None,
    min_score: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """View lead qualification scores across workspace companies."""
    filters = [Company.workspace_id == workspace_id]
    if is_qualified is not None:
        filters.append(LeadScore.is_qualified == is_qualified)
    if min_score is not None:
        filters.append(LeadScore.total_score >= min_score)

    query = (
        select(LeadScore)
        .join(Company, LeadScore.company_id == Company.id)
        .where(and_(*filters))
        .order_by(LeadScore.total_score.desc())
        .limit(limit)
        .options(selectinload(LeadScore.explanations))
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{company_id}/score", response_model=LeadScoreResponse)
async def get_lead_score(
    company_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """Get transparent 5-dimension score breakdown and rationale for a company."""
    repo = LeadRepository(db)
    score = await repo.get_by_company(company_id)
    if not score:
        raise HTTPException(status_code=404, detail="Lead score not found for this company.")
    return score


@router.put("/{company_id}/score", response_model=LeadScoreResponse)
async def override_lead_score(
    company_id: str,
    data: LeadScoreOverride,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """Manually adjust qualification score or qualification decision."""
    repo = LeadRepository(db)
    score = await repo.get_by_company(company_id)
    if not score:
        raise HTTPException(status_code=404, detail="Lead score not found for this company.")

    score.total_score = data.total_score
    score.is_qualified = data.is_qualified
    if data.qualification_notes:
        score.qualification_notes = data.qualification_notes

    await db.commit()
    await db.refresh(score)
    return score
