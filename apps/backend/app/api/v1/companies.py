from typing import List, Optional
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace_id
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.company import Company
from app.models.workspace import User
from app.repositories.company_repo import CompanyRepository
from app.repositories.lead_repo import LeadRepository
from app.schemas.common import PaginatedResponse
from app.schemas.company import (
    CompanyCreate,
    CompanyDetailResponse,
    CompanyResponse,
    CompanyUpdate,
    FactResponse,
)
from app.schemas.lead import ActivityResponse

router = APIRouter(prefix="/companies", tags=["Companies & Intelligence"])


@router.get("", response_model=PaginatedResponse[CompanyResponse])
async def list_companies(
    status: Optional[str] = None,
    industry: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """Query company directory with filters and search."""
    repo = CompanyRepository(db)
    skip = (page - 1) * page_size
    items = await repo.list_companies(
        workspace_id=workspace_id,
        status=status,
        industry=industry,
        search=search,
        skip=skip,
        limit=page_size,
    )
    total = await repo.count_companies(workspace_id=workspace_id, status=status, industry=industry, search=search)

    return PaginatedResponse(
        items=[CompanyResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 1,
    )


@router.post("", response_model=CompanyResponse)
async def create_company(
    data: CompanyCreate,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """Seed or create a company record from target URL or domain."""
    repo = CompanyRepository(db)
    raw_url = data.target_url.strip()
    if not (raw_url.startswith("http://") or raw_url.startswith("https://")):
        raw_url = "https://" + raw_url
    domain = urlparse(raw_url).netloc.lower()

    company = await repo.upsert_company(
        workspace_id=workspace_id,
        name=data.name or domain,
        primary_domain=domain,
        description=data.description,
        industry=data.industry,
    )
    await db.commit()
    await db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyDetailResponse)
async def get_company_details(
    company_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """Fetch complete company intelligence profile, facts, reports, and scores."""
    repo = CompanyRepository(db)
    company = await repo.get_with_details(workspace_id, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    response = CompanyDetailResponse.model_validate(company)
    if company.lead_score:
        response.total_score = company.lead_score.total_score
        response.is_qualified = company.lead_score.is_qualified

    return response


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    data: CompanyUpdate,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """Update company details or CRM pipeline status."""
    repo = CompanyRepository(db)
    company = await repo.get_with_details(workspace_id, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    if data.name is not None:
        company.name = data.name
    if data.industry is not None:
        company.industry = data.industry
    if data.employee_range is not None:
        company.employee_range = data.employee_range
    if data.description is not None:
        company.description = data.description
    if data.headquarters is not None:
        company.headquarters = data.headquarters
    if data.status is not None:
        company.status = data.status
    if data.pipeline_stage_id is not None:
        company.pipeline_stage_id = data.pipeline_stage_id

    await db.commit()
    await db.refresh(company)
    return company


@router.delete("/{company_id}")
async def delete_company(
    company_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN"])),
):
    """Delete company and cascade all associated data."""
    repo = CompanyRepository(db)
    company = await repo.get_with_details(workspace_id, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    await repo.delete(company)
    await db.commit()
    return {"message": "Company deleted successfully", "id": company_id}


@router.get("/{company_id}/facts", response_model=List[FactResponse])
async def list_company_facts(
    company_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """Retrieve verified and provisional facts with citations."""
    repo = CompanyRepository(db)
    company = await repo.get_with_details(workspace_id, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    return [FactResponse.model_validate(f) for f in company.facts]


@router.get("/{company_id}/activities", response_model=List[ActivityResponse])
async def list_company_activities(
    company_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """Retrieve CRM activity history and audit timeline for company."""
    lead_repo = LeadRepository(db)
    activities = await lead_repo.list_activities(workspace_id, company_id=company_id)
    return [ActivityResponse.model_validate(a) for a in activities]
