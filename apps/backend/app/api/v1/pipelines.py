from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace_id
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.workspace import User
from app.repositories.lead_repo import LeadRepository
from app.schemas.lead import PipelineResponse

router = APIRouter(prefix="/pipelines", tags=["CRM Pipelines & Stages"])


@router.get("", response_model=List[PipelineResponse])
async def list_pipelines(
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """Retrieve all sales pipelines and configured Kanban stages."""
    repo = LeadRepository(db)
    # Ensure default pipeline exists
    await repo.get_or_create_default_pipeline(workspace_id)
    await db.commit()
    pipelines = await repo.list_pipelines(workspace_id)
    return pipelines
