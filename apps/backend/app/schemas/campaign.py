from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    name: str
    subject_template: str
    body_template: str
    variables: Optional[str] = None


class TemplateResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    subject_template: str
    body_template: str
    variables: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    name: str
    template_id: Optional[str] = None
    auto_send_enabled: bool = False
    daily_limit: int = Field(default=50, ge=1, le=1000)


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None  # DRAFT, ACTIVE, PAUSED, COMPLETED
    auto_send_enabled: Optional[bool] = None
    daily_limit: Optional[int] = None


class CampaignResponse(BaseModel):
    id: str
    workspace_id: str
    template_id: Optional[str] = None
    name: str
    status: str
    auto_send_enabled: bool
    daily_limit: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
