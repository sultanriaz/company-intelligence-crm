from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class ContactBase(BaseModel):
    first_name: str
    last_name: str = ""
    email: EmailStr
    title: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    provenance_url: Optional[str] = None
    permission_status: str = "LEGITIMATE_INTEREST"
    is_suppressed: bool = False


class ContactCreate(ContactBase):
    company_id: str


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    permission_status: Optional[str] = None
    is_suppressed: Optional[bool] = None


class ContactResponse(ContactBase):
    id: str
    workspace_id: str
    company_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
