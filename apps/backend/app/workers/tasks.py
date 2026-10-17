import asyncio
from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.orchestration.engine import orchestration_engine
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.run_company_research_task", bind=True, max_retries=2)
def run_company_research_task(
    self,
    workspace_id: str,
    target_url: str,
    company_name: str = None,
    crawl_depth: int = 2,
    max_pages: int = 15,
    include_email_generation: bool = True,
):
    """Celery background task for multi-agent company research."""
    logger.info(f"Starting Celery task for target: {target_url} (workspace: {workspace_id})")

    async def _runner():
        async with AsyncSessionLocal() as session:
            result = await orchestration_engine.start_research_run(
                session=session,
                workspace_id=workspace_id,
                target_url=target_url,
                company_name=company_name,
                crawl_depth=crawl_depth,
                max_pages=max_pages,
                include_email_generation=include_email_generation,
                triggered_by="CELERY_WORKER",
            )
            await session.commit()
            return result.model_dump()

    try:
        return asyncio.run(_runner())
    except Exception as exc:
        logger.error(f"Celery research task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="app.workers.tasks.dispatch_outbox_batch_task")
def dispatch_outbox_batch_task():
    """Celery background task to poll and dispatch pending transactional outbox messages."""
    logger.info("Executing periodic transactional outbox polling...")

    async def _runner():
        from app.models.email import EmailDraft
        from app.email.outbox import outbox_service
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            # Query approved drafts that are ready for sending
            query = select(EmailDraft).where(EmailDraft.status == "APPROVED").limit(20)
            res = await session.execute(query)
            drafts = res.scalars().all()

            dispatched_count = 0
            for draft in drafts:
                try:
                    await outbox_service.stage_and_dispatch(
                        session=session,
                        workspace_id=draft.contact.workspace_id,
                        draft=draft,
                        is_approved=True,
                    )
                    dispatched_count += 1
                except Exception as e:
                    logger.error(f"Error dispatching approved draft {draft.id}: {str(e)}")

            await session.commit()
            return {"dispatched": dispatched_count}

    return asyncio.run(_runner())


@celery_app.task(name="app.workers.tasks.recrawl_scheduled_company_task")
def recrawl_scheduled_company_task(workspace_id: str, target_url: str):
    """Celery background task to periodically re-crawl companies for incremental updates."""
    return run_company_research_task(
        workspace_id=workspace_id,
        target_url=target_url,
        crawl_depth=2,
        max_pages=15,
        include_email_generation=False,
    )
