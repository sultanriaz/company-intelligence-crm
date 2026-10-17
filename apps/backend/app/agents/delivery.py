from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.email.outbox import outbox_service
from app.models.email import EmailDraft
from app.schemas.contracts import EmailDeliveryResult


class EmailDeliveryAgent(BaseAgent):
    """
    Agent 10: Email Delivery Agent.
    Executes authorized delivery workflows via transactional outbox,
    applying lawful basis checks, suppression enforcement, and provider dispatch.
    """

    def __init__(self):
        super().__init__(name="EmailDeliveryAgent")

    async def execute_task(
        self,
        session: AsyncSession,
        workspace_id: str,
        draft: EmailDraft,
        is_campaign_active: bool = True,
        is_approved: bool = False,
    ) -> EmailDeliveryResult:
        result = await outbox_service.stage_and_dispatch(
            session=session,
            workspace_id=workspace_id,
            draft=draft,
            is_campaign_active=is_campaign_active,
            is_approved=is_approved,
        )
        return result


delivery_agent = EmailDeliveryAgent()
