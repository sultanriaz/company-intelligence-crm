from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace_id
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.workspace import User
from app.repositories.email_repo import EmailRepository
from app.schemas.campaign import (
    CampaignCreate,
    CampaignResponse,
    CampaignUpdate,
    TemplateCreate,
    TemplateResponse,
)

router = APIRouter(prefix="/campaigns", tags=["Outreach Campaigns"])


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[str] = None,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """List outreach campaigns."""
    repo = EmailRepository(db)
    return await repo.list_campaigns(workspace_id, status=status)


@router.post("", response_model=CampaignResponse)
async def create_campaign(
    data: CampaignCreate,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """Create a new outreach campaign."""
    repo = EmailRepository(db)
    campaign = await repo.create_campaign(
        workspace_id=workspace_id,
        name=data.name,
        template_id=data.template_id,
        auto_send_enabled=data.auto_send_enabled,
        daily_limit=data.daily_limit,
    )
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """List email templates."""
    repo = EmailRepository(db)
    return await repo.list_templates(workspace_id)


@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """Create a new Jinja2 email template."""
    repo = EmailRepository(db)
    template = await repo.create_template(
        workspace_id=workspace_id,
        name=data.name,
        subject_template=data.subject_template,
        body_template=data.body_template,
        variables=data.variables,
    )
    await db.commit()
    await db.refresh(template)
    return template


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """Get single campaign details."""
    repo = EmailRepository(db)
    campaign = await repo.get_campaign(workspace_id, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    data: CampaignUpdate,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """Update campaign parameters (activation, daily limits, status)."""
    repo = EmailRepository(db)
    campaign = await repo.get_campaign(workspace_id, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    if data.name is not None:
        campaign.name = data.name
    if data.status is not None:
        campaign.status = data.status
    if data.auto_send_enabled is not None:
        campaign.auto_send_enabled = data.auto_send_enabled
    if data.daily_limit is not None:
        campaign.daily_limit = data.daily_limit

    await db.commit()
    await db.refresh(campaign)
    return campaign
