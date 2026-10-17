from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import (
    AppBaseException,
    AuthenticationFailedException,
    DuplicateEntityException,
    EmailComplianceViolationException,
    PermissionDeniedException,
    RateLimitExceededException,
    ResourceNotFoundException,
    SSRFViolationException,
    WorkflowExecutionException,
)
from app.core.logging import setup_logging, logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging(settings.LOG_LEVEL)
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode...")
    # Initialize DB schema for dev/test sqlite environments
    await init_db()
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade AI Multi-Agent Company Intelligence, CRM & Email Automation Platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


# Domain Exception Handlers
@app.exception_handler(SSRFViolationException)
async def ssrf_exception_handler(request: Request, exc: SSRFViolationException):
    logger.warning(f"SSRF violation blocked: {exc.message} on {request.url}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "SSRF_VIOLATION", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(RateLimitExceededException)
async def ratelimit_exception_handler(request: Request, exc: RateLimitExceededException):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "RATE_LIMIT_EXCEEDED", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(EmailComplianceViolationException)
async def compliance_exception_handler(request: Request, exc: EmailComplianceViolationException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "EMAIL_COMPLIANCE_VIOLATION", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(ResourceNotFoundException)
async def not_found_exception_handler(request: Request, exc: ResourceNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "RESOURCE_NOT_FOUND", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(PermissionDeniedException)
async def permission_exception_handler(request: Request, exc: PermissionDeniedException):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"error": "PERMISSION_DENIED", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(AuthenticationFailedException)
async def auth_exception_handler(request: Request, exc: AuthenticationFailedException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": "AUTHENTICATION_FAILED", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(AppBaseException)
async def app_base_exception_handler(request: Request, exc: AppBaseException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": type(exc).__name__, "message": exc.message, "details": exc.details},
    )


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "documentation": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }
