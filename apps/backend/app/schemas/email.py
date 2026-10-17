from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class EmailDraftResponse(BaseModel):
    id: str
    campaign_id: Optional[str] = None
    contact_id: str
    subject: str
    body_html: str
    body_text: str
    referenced_facts: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailApprovalRequest(BaseModel):
    decision: str = Field(description="APPROVED or REJECTED")
    feedback: Optional[str] = None


class EmailMessageResponse(BaseModel):
    id: str
    workspace_id: str
    draft_id: Optional[str] = None
    contact_id: str
    provider_name: str
    provider_message_id: Optional[str] = None
    idempotency_key: str
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SuppressionCreate(BaseModel):
    email: EmailStr
    reason: str = "MANUAL"


class SuppressionResponse(BaseModel):
    id: str
    workspace_id: str
    email: str
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


class SendTestEmailRequest(BaseModel):
    to_email: EmailStr
    subject: str = "Test Email from Company Intelligence"
    body_text: str = "This is a test sandbox email dispatched from the outreach engine."
