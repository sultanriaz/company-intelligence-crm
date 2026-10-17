from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CompanyBase(BaseModel):
    name: str
    primary_domain: str
    legal_name: Optional[str] = None
    industry: Optional[str] = None
    employee_range: Optional[str] = None
    description: Optional[str] = None
    headquarters: Optional[str] = None
    status: str = "PROSPECT"
    pipeline_stage_id: Optional[str] = None


class CompanyCreate(BaseModel):
    name: Optional[str] = None
    target_url: str
    industry: Optional[str] = None
    description: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    employee_range: Optional[str] = None
    description: Optional[str] = None
    headquarters: Optional[str] = None
    status: Optional[str] = None
    pipeline_stage_id: Optional[str] = None


class FactResponse(BaseModel):
    id: str
    field_name: str
    field_value: str
    source_url: str
    confidence_score: float
    verification_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    id: str
    executive_summary: str
    challenges_hypotheses: Optional[str] = None
    opportunities: Optional[str] = None
    tech_stack: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyResponse(CompanyBase):
    id: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyDetailResponse(CompanyResponse):
    facts: List[FactResponse] = Field(default_factory=list)
    reports: List[ReportResponse] = Field(default_factory=list)
    total_score: Optional[int] = None
    is_qualified: Optional[bool] = None
