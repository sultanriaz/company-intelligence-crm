from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog, IntegrationConfig, ScheduledTask, WebhookEvent
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def log_action(
        self,
        workspace_id: str,
        action: str,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[str] = None,
    ) -> AuditLog:
        log = AuditLog(
            workspace_id=workspace_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            details=details,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_logs(
        self,
        workspace_id: str,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[AuditLog]:
        filters = [AuditLog.workspace_id == workspace_id]
        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)
        if action:
            filters.append(AuditLog.action == action)

        query = (
            select(AuditLog)
            .where(and_(*filters))
            .order_by(AuditLog.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # Webhook Events
    async def record_webhook_event(
        self, provider: str, event_id: str, payload_json: str
    ) -> WebhookEvent:
        query = select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        result = await self.session.execute(query)
        existing = result.scalars().first()
        if existing:
            return existing

        event = WebhookEvent(
            provider=provider,
            event_id=event_id,
            payload=payload_json,
            status="PROCESSED",
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def is_webhook_duplicate(self, event_id: str) -> bool:
        query = select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        result = await self.session.execute(query)
        return result.scalars().first() is not None
