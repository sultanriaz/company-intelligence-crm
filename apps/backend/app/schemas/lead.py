from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ExplanationResponse(BaseModel):
    dimension: str
    score_assigned: int
    max_score: int
    reason: str

    class Config:
        from_attributes = True


class LeadScoreResponse(BaseModel):
    id: str
    company_id: str
    total_score: int
    industry_score: int
    service_score: int
    scale_score: int
    opportunity_score: int
    evidence_score: int
    is_qualified: bool
    qualification_notes: Optional[str] = None
    scored_at: datetime
    explanations: List[ExplanationResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class LeadScoreOverride(BaseModel):
    total_score: int = Field(ge=0, le=100)
    is_qualified: bool
    qualification_notes: Optional[str] = None


class PipelineStageResponse(BaseModel):
    id: str
    name: str
    order_index: int
    color: str

    class Config:
        from_attributes = True


class PipelineResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    is_default: bool
    stages: List[PipelineStageResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ActivityCreate(BaseModel):
    company_id: str
    contact_id: Optional[str] = None
    activity_type: str
    details: str


class ActivityResponse(BaseModel):
    id: str
    workspace_id: str
    company_id: str
    contact_id: Optional[str] = None
    activity_type: str
    details: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True
