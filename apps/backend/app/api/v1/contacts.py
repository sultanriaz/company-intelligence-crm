from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace_id
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.contact import Contact
from app.models.workspace import User
from app.repositories.contact_repo import ContactRepository
from app.schemas.common import PaginatedResponse
from app.schemas.contact import ContactCreate, ContactResponse, ContactUpdate

router = APIRouter(prefix="/contacts", tags=["Contacts & People"])


@router.get("", response_model=PaginatedResponse[ContactResponse])
async def list_contacts(
    company_id: Optional[str] = None,
    is_suppressed: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """Query contact directory with filters."""
    repo = ContactRepository(db)
    skip = (page - 1) * page_size
    items = await repo.list_contacts(
        workspace_id=workspace_id,
        company_id=company_id,
        is_suppressed=is_suppressed,
        skip=skip,
        limit=page_size,
    )
    total = await repo.count_contacts(workspace_id=workspace_id, company_id=company_id, is_suppressed=is_suppressed)

    return PaginatedResponse(
        items=[ContactResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 1,
    )


@router.post("", response_model=ContactResponse)
async def create_contact(
    data: ContactCreate,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """Create a new contact associated with a company."""
    repo = ContactRepository(db)
    contact = await repo.upsert_contact(
        workspace_id=workspace_id,
        company_id=data.company_id,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        title=data.title,
        phone=data.phone,
        linkedin_url=data.linkedin_url,
        provenance_url=data.provenance_url,
        permission_status=data.permission_status,
    )
    await db.commit()
    await db.refresh(contact)
    return contact


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """Get single contact by ID."""
    repo = ContactRepository(db)
    contact = await repo.get_by_id(contact_id)
    if not contact or contact.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Contact not found.")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    data: ContactUpdate,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """Update contact attributes."""
    repo = ContactRepository(db)
    contact = await repo.get_by_id(contact_id)
    if not contact or contact.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Contact not found.")

    if data.first_name is not None:
        contact.first_name = data.first_name
    if data.last_name is not None:
        contact.last_name = data.last_name
    if data.title is not None:
        contact.title = data.title
    if data.phone is not None:
        contact.phone = data.phone
    if data.linkedin_url is not None:
        contact.linkedin_url = data.linkedin_url
    if data.permission_status is not None:
        contact.permission_status = data.permission_status
    if data.is_suppressed is not None:
        contact.is_suppressed = data.is_suppressed

    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN"])),
):
    """Delete contact."""
    repo = ContactRepository(db)
    contact = await repo.get_by_id(contact_id)
    if not contact or contact.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Contact not found.")

    await repo.delete(contact)
    await db.commit()
    return {"message": "Contact deleted successfully", "id": contact_id}
