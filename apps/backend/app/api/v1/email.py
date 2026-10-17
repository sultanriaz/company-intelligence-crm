from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace_id
from app.auth.dependencies import require_roles
from app.core.config import settings
from app.core.database import get_db
from app.email.outbox import outbox_service
from app.email.providers import get_email_provider
from app.models.workspace import User
from app.repositories.email_repo import EmailRepository
from app.schemas.contracts import EmailDeliveryResult
from app.schemas.email import (
    EmailApprovalRequest,
    EmailDraftResponse,
    SendTestEmailRequest,
    SuppressionCreate,
    SuppressionResponse,
)

router = APIRouter(prefix="/email", tags=["Email Governance & Delivery"])


@router.get("/drafts", response_model=List[EmailDraftResponse])
async def list_drafts(
    status: Optional[str] = None,
    campaign_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """List pending or reviewed outreach drafts."""
    repo = EmailRepository(db)
    skip = (page - 1) * page_size
    drafts = await repo.list_drafts(status=status, campaign_id=campaign_id, skip=skip, limit=page_size)
    return [EmailDraftResponse.model_validate(d) for d in drafts]


@router.get("/drafts/{draft_id}", response_model=EmailDraftResponse)
async def get_draft(
    draft_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """Get single email draft details."""
    repo = EmailRepository(db)
    draft = await repo.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Email draft not found.")
    return draft


@router.post("/approvals/{draft_id}", response_model=EmailDeliveryResult)
async def decide_draft_approval(
    draft_id: str,
    data: EmailApprovalRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    current_user: User = Depends(require_roles(["ADMIN", "MEMBER"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit human review decision (APPROVED / REJECTED) for an email draft.
    If APPROVED, stages message in transactional outbox and dispatches via active provider.
    """
    decision = data.decision.strip().upper()
    if decision not in {"APPROVED", "REJECTED"}:
        raise HTTPException(status_code=400, detail="Decision must be 'APPROVED' or 'REJECTED'.")

    repo = EmailRepository(db)
    draft = await repo.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Email draft not found.")

    # Record review decision
    await repo.record_approval(
        draft_id=draft.id,
        reviewed_by=current_user.full_name or current_user.email,
        decision=decision,
        feedback=data.feedback,
    )

    if decision == "REJECTED":
        await db.commit()
        return EmailDeliveryResult(
            message_id="",
            idempotency_key="",
            provider="none",
            delivery_status="REJECTED",
            error=f"Rejected by reviewer: {data.feedback or 'No feedback provided'}",
        )

    # If APPROVED: dispatch via Outbox
    result = await outbox_service.stage_and_dispatch(
        session=db,
        workspace_id=workspace_id,
        draft=draft,
        is_approved=True,
    )
    await db.commit()
    return result


@router.post("/messages/send-test")
async def send_test_email(
    data: SendTestEmailRequest,
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """Dispatches a test sandbox message through the configured provider."""
    provider = get_email_provider()
    result = await provider.send_email(
        to_email=data.to_email,
        subject=data.subject,
        body_text=data.body_text,
        body_html=f"<p>{data.body_text}</p>",
        from_address=settings.EMAIL_FROM_ADDRESS,
        from_name=settings.EMAIL_FROM_NAME,
        reply_to=settings.EMAIL_REPLY_TO,
        idempotency_key=f"test-{data.to_email}",
    )
    return {
        "success": result.success,
        "provider": result.provider_name,
        "status": result.status,
        "message_id": result.provider_message_id,
        "error": result.error_message,
    }


@router.get("/suppressions", response_model=List[SuppressionResponse])
async def list_suppressions(
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER", "VIEWER"])),
):
    """View active email suppression list."""
    repo = EmailRepository(db)
    items = await repo.list_suppressions(workspace_id)
    return [SuppressionResponse.model_validate(s) for s in items]


@router.post("/suppressions", response_model=SuppressionResponse)
async def add_suppression(
    data: SuppressionCreate,
    workspace_id: str = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN", "MEMBER"])),
):
    """Manually add an email to the workspace suppression list."""
    repo = EmailRepository(db)
    supp = await repo.add_suppression(workspace_id, data.email, reason=data.reason)
    await db.commit()
    await db.refresh(supp)
    return supp
