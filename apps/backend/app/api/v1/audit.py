from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace_id
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.workspace import User
from app.repositories.audit_repo import AuditRepository

router = APIRouter(prefix="/audit", tags=["Security & Audit Logs"])


class AuditLogResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN"])),
):
    """Retrieve workspace audit trails."""
    repo = AuditRepository(db)
    logs = await repo.list_logs(workspace_id, resource_type=resource_type, action=action, limit=limit)
    return [AuditLogResponse.model_validate(l) for l in logs]
