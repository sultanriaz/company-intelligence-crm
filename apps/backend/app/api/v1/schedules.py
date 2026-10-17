from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace_id
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.audit import ScheduledTask
from app.models.workspace import User

router = APIRouter(prefix="/schedules", tags=["Task Scheduling"])


class ScheduledTaskCreate(BaseModel):
    task_type: str  # RE_CRAWL, FOLLOW_UP, METRICS_AGGREGATION
    schedule_cron: str
    payload: Optional[str] = None


class ScheduledTaskResponse(BaseModel):
    id: str
    workspace_id: str
    task_type: str
    schedule_cron: str
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[ScheduledTaskResponse])
async def list_scheduled_tasks(
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """List recurring scheduled tasks."""
    query = select(ScheduledTask).where(ScheduledTask.workspace_id == workspace_id).order_by(ScheduledTask.created_at.desc())
    res = await db.execute(query)
    return list(res.scalars().all())


@router.post("", response_model=ScheduledTaskResponse)
async def create_scheduled_task(
    data: ScheduledTaskCreate,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN"])),
):
    """Create a recurring scheduled job."""
    task = ScheduledTask(
        workspace_id=workspace_id,
        task_type=data.task_type,
        schedule_cron=data.schedule_cron,
        payload=data.payload,
        is_active=True,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}")
async def delete_scheduled_task(
    task_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN"])),
):
    """Delete a scheduled task."""
    query = select(ScheduledTask).where(ScheduledTask.id == task_id, ScheduledTask.workspace_id == workspace_id)
    res = await db.execute(query)
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found.")

    await db.delete(task)
    await db.commit()
    return {"message": "Scheduled task deleted", "id": task_id}
