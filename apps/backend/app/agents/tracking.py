from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.email.tracking import tracking_processor


class EmailTrackingAgent(BaseAgent):
    """
    Agent 11: Email Tracking / Follow-Up Agent.
    Processes authenticated webhook events, updates contact timelines,
    and enforces real-time suppressions on bounces or opt-outs.
    """

    def __init__(self):
        super().__init__(name="EmailTrackingAgent")

    async def execute_task(
        self,
        session: AsyncSession,
        provider: str,
        event_id: str,
        event_type: str,
        recipient_email: str,
        provider_message_id: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        return await tracking_processor.process_event(
            session=session,
            provider=provider,
            event_id=event_id,
            event_type=event_type,
            recipient_email=recipient_email,
            provider_message_id=provider_message_id,
            raw_payload=raw_payload,
        )


tracking_agent = EmailTrackingAgent()
