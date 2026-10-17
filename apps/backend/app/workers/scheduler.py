import asyncio
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.models.audit import ScheduledTask
from app.orchestration.engine import orchestration_engine


class InProcessScheduler:
    """
    Lightweight asynchronous background scheduler.
    Allows running recurring scheduled research and outbox polling
    in standalone local deployments without an external Celery Beat daemon.
    """

    def __init__(self, poll_interval_seconds: int = 60):
        self.poll_interval = poll_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"In-process task scheduler started (interval: {self.poll_interval}s).")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("In-process task scheduler stopped.")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception as e:
                logger.error(f"Error in scheduler loop tick: {str(e)}")
            await asyncio.sleep(self.poll_interval)

    async def _tick(self) -> None:
        async with AsyncSessionLocal() as session:
            now = datetime.now(timezone.utc)
            query = select(ScheduledTask).where(
                ScheduledTask.is_active == True,
            )
            res = await session.execute(query)
            tasks = res.scalars().all()

            for task in tasks:
                if task.next_run_at is None or task.next_run_at <= now:
                    logger.info(f"Triggering scheduled task: {task.task_type} (id: {task.id})")
                    task.last_run_at = now
                    # For demonstration, set next run in 24 hours
                    from datetime import timedelta
                    task.next_run_at = now + timedelta(hours=24)
            await session.commit()


scheduler = InProcessScheduler()
