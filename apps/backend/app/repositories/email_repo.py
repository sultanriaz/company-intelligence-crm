from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import EmailTemplate, EmailCampaign, CampaignRecipient
from app.models.email import EmailDraft, EmailApproval, EmailMessage, EmailEvent, EmailSuppression
from app.repositories.base import BaseRepository


class EmailRepository(BaseRepository[EmailMessage]):
    def __init__(self, session: AsyncSession):
        super().__init__(EmailMessage, session)

    # Templates
    async def create_template(
        self, workspace_id: str, name: str, subject_template: str, body_template: str, variables: Optional[str] = None
    ) -> EmailTemplate:
        template = EmailTemplate(
            workspace_id=workspace_id,
            name=name,
            subject_template=subject_template,
            body_template=body_template,
            variables=variables,
        )
        self.session.add(template)
        await self.session.flush()
        return template

    async def get_template(self, workspace_id: str, template_id: str) -> Optional[EmailTemplate]:
        query = select(EmailTemplate).where(
            and_(EmailTemplate.workspace_id == workspace_id, EmailTemplate.id == template_id)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_templates(self, workspace_id: str) -> List[EmailTemplate]:
        query = select(EmailTemplate).where(EmailTemplate.workspace_id == workspace_id).order_by(EmailTemplate.name.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # Campaigns
    async def create_campaign(
        self, workspace_id: str, name: str, template_id: Optional[str] = None, auto_send_enabled: bool = False, daily_limit: int = 50
    ) -> EmailCampaign:
        campaign = EmailCampaign(
            workspace_id=workspace_id,
            name=name,
            template_id=template_id,
            auto_send_enabled=auto_send_enabled,
            daily_limit=daily_limit,
            status="DRAFT",
        )
        self.session.add(campaign)
        await self.session.flush()
        return campaign

    async def get_campaign(self, workspace_id: str, campaign_id: str) -> Optional[EmailCampaign]:
        query = (
            select(EmailCampaign)
            .where(and_(EmailCampaign.workspace_id == workspace_id, EmailCampaign.id == campaign_id))
            .options(selectinload(EmailCampaign.recipients), selectinload(EmailCampaign.drafts))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_campaigns(self, workspace_id: str, status: Optional[str] = None) -> List[EmailCampaign]:
        filters = [EmailCampaign.workspace_id == workspace_id]
        if status:
            filters.append(EmailCampaign.status == status)
        query = select(EmailCampaign).where(and_(*filters)).order_by(EmailCampaign.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # Drafts
    async def create_draft(
        self,
        contact_id: str,
        subject: str,
        body_html: str,
        body_text: str,
        campaign_id: Optional[str] = None,
        referenced_facts: Optional[str] = None,
    ) -> EmailDraft:
        draft = EmailDraft(
            contact_id=contact_id,
            campaign_id=campaign_id,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            referenced_facts=referenced_facts,
            status="PENDING_APPROVAL",
        )
        self.session.add(draft)
        await self.session.flush()
        return draft

    async def get_draft(self, draft_id: str) -> Optional[EmailDraft]:
        query = (
            select(EmailDraft)
            .where(EmailDraft.id == draft_id)
            .options(selectinload(EmailDraft.contact), selectinload(EmailDraft.approvals))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_drafts(
        self,
        status: Optional[str] = None,
        campaign_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[EmailDraft]:
        filters = []
        if status:
            filters.append(EmailDraft.status == status)
        if campaign_id:
            filters.append(EmailDraft.campaign_id == campaign_id)

        query = (
            select(EmailDraft)
            .where(and_(*filters))
            .order_by(EmailDraft.created_at.desc())
            .offset(skip)
            .limit(limit)
            .options(selectinload(EmailDraft.contact))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def record_approval(
        self, draft_id: str, reviewed_by: str, decision: str, feedback: Optional[str] = None
    ) -> EmailApproval:
        approval = EmailApproval(
            draft_id=draft_id,
            reviewed_by=reviewed_by,
            decision=decision,
            feedback=feedback,
        )
        self.session.add(approval)
        draft = await self.get_draft(draft_id)
        if draft:
            draft.status = decision
        await self.session.flush()
        return approval

    # Suppressions
    async def is_suppressed(self, workspace_id: str, email: str) -> bool:
        normalized = email.strip().lower()
        query = select(EmailSuppression).where(
            and_(EmailSuppression.workspace_id == workspace_id, EmailSuppression.email == normalized)
        )
        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def add_suppression(self, workspace_id: str, email: str, reason: str = "MANUAL") -> EmailSuppression:
        normalized = email.strip().lower()
        query = select(EmailSuppression).where(
            and_(EmailSuppression.workspace_id == workspace_id, EmailSuppression.email == normalized)
        )
        result = await self.session.execute(query)
        existing = result.scalars().first()
        if existing:
            return existing

        suppression = EmailSuppression(
            workspace_id=workspace_id,
            email=normalized,
            reason=reason,
        )
        self.session.add(suppression)
        await self.session.flush()
        return suppression

    async def list_suppressions(self, workspace_id: str) -> List[EmailSuppression]:
        query = (
            select(EmailSuppression)
            .where(EmailSuppression.workspace_id == workspace_id)
            .order_by(EmailSuppression.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # Messages & Double-Send Prevention
    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[EmailMessage]:
        query = select(EmailMessage).where(EmailMessage.idempotency_key == idempotency_key)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def create_message(
        self,
        workspace_id: str,
        contact_id: str,
        idempotency_key: str,
        draft_id: Optional[str] = None,
        provider_name: str = "mock",
    ) -> EmailMessage:
        message = EmailMessage(
            workspace_id=workspace_id,
            contact_id=contact_id,
            draft_id=draft_id,
            idempotency_key=idempotency_key,
            provider_name=provider_name,
            status="PENDING",
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def record_event(
        self, message_id: str, event_type: str, payload_json: Optional[str] = None
    ) -> EmailEvent:
        event = EmailEvent(
            email_message_id=message_id,
            event_type=event_type,
            payload=payload_json,
        )
        self.session.add(event)
        await self.session.flush()
        return event
