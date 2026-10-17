from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.companies import router as companies_router
from app.api.v1.contacts import router as contacts_router
from app.api.v1.research import router as research_router
from app.api.v1.agents import router as agents_router
from app.api.v1.leads import router as leads_router
from app.api.v1.pipelines import router as pipelines_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.email import router as email_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.schedules import router as schedules_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.audit import router as audit_router
from app.api.v1.health import router as health_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(companies_router)
api_v1_router.include_router(contacts_router)
api_v1_router.include_router(research_router)
api_v1_router.include_router(agents_router)
api_v1_router.include_router(leads_router)
api_v1_router.include_router(pipelines_router)
api_v1_router.include_router(campaigns_router)
api_v1_router.include_router(email_router)
api_v1_router.include_router(integrations_router)
api_v1_router.include_router(schedules_router)
api_v1_router.include_router(webhooks_router)
api_v1_router.include_router(audit_router)
