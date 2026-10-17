from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace_id
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.workspace import User
from app.schemas.auth import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("", response_model=List[UserResponse])
async def list_workspace_users(
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """List all users within the current workspace."""
    query = select(User).where(User.workspace_id == workspace_id).order_by(User.created_at.desc())
    res = await db.execute(query)
    return list(res.scalars().all())


@router.post("", response_model=UserResponse)
async def create_workspace_user(
    data: UserCreate,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN"])),
):
    """Add a new user to the workspace (Admin only)."""
    existing_query = select(User).where(User.email == data.email.lower())
    res = await db.execute(existing_query)
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    new_user = User(
        workspace_id=workspace_id,
        email=data.email.lower(),
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        role=data.role,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
