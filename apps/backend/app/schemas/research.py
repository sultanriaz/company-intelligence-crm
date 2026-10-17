from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ResearchRunCreate(BaseModel):
    target_url: str
    company_name: Optional[str] = None
    crawl_depth: int = Field(default=2, ge=1, le=5)
    max_pages: int = Field(default=15, ge=1, le=50)
    include_email_generation: bool = True


class AgentExecutionResponse(BaseModel):
    id: str
    agent_name: str
    state: str
    tokens_used: int
    cost_usd: float
    duration_ms: int
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowCheckpointResponse(BaseModel):
    id: str
    state: str
    step_index: int
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchRunResponse(BaseModel):
    id: str
    workspace_id: str
    company_id: Optional[str] = None
    target_url: str
    status: str
    triggered_by: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    executions: List[AgentExecutionResponse] = Field(default_factory=list)
    checkpoints: List[WorkflowCheckpointResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
