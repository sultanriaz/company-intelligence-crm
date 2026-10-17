from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "company_intelligence_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.AGENT_MAX_EXECUTION_SECONDS + 30,
    task_soft_time_limit=settings.AGENT_MAX_EXECUTION_SECONDS,
    task_routes={
        "app.workers.tasks.run_company_research_task": {"queue": "research"},
        "app.workers.tasks.dispatch_outbox_batch_task": {"queue": "email"},
        "app.workers.tasks.recrawl_scheduled_company_task": {"queue": "research"},
    },
    beat_schedule={
        "dispatch-outbox-every-minute": {
            "task": "app.workers.tasks.dispatch_outbox_batch_task",
            "schedule": 60.0,
        },
    },
)
