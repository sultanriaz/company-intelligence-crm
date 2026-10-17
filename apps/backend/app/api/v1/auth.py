from datetime import timedelta
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.workspace import User, Workspace
from app.repositories.lead_repo import LeadRepository
from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication & Workspaces"])


def slugify(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"[^\w\s-]", "", text).replace(" ", "-")


@router.post("/register", response_model=UserResponse)
async def register_workspace_admin(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new workspace and root administrator account."""
    workspace_name = data.workspace_name or "Default Workspace"
    base_slug = slugify(workspace_name)
    slug = base_slug

    # Check existing user
    existing_user_query = select(User).where(User.email == data.email.lower())
    res = await db.execute(existing_user_query)
    if res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Find or create workspace
    ws_query = select(Workspace).where(Workspace.slug == slug)
    res_ws = await db.execute(ws_query)
    workspace = res_ws.scalars().first()

    if not workspace:
        workspace = Workspace(name=workspace_name, slug=slug)
        db.add(workspace)
        await db.flush()

        # Initialize default CRM sales pipeline
        lead_repo = LeadRepository(db)
        await lead_repo.get_or_create_default_pipeline(workspace.id)

    # Create admin user
    user = User(
        workspace_id=workspace.id,
        email=data.email.lower(),
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        role=data.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login_for_access_token(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticates user credentials and returns signed JWT token."""
    query = select(User).where(User.email == data.email.lower())
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated.",
        )

    access_token = create_access_token(
        subject=user.id,
        workspace_id=user.workspace_id,
        role=user.role,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        workspace_id=user.workspace_id,
        role=user.role,
    )


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Returns currently authenticated user profile."""
    return current_user
