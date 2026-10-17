import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set environment before loading application
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SYNC_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMAIL_PROVIDER"] = "mock"
os.environ["EMAIL_DRY_RUN"] = "true"
os.environ["EMAIL_WEBHOOK_SECRET"] = "test-webhook-secret-signing-key"

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.workspace import User, Workspace
from app.repositories.lead_repo import LeadRepository

# Test in-memory async SQLite engine
test_async_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True,
)
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        yield session
        await session.rollback()

    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def seed_data(db_session: AsyncSession):
    # Workspace
    workspace = Workspace(name="Test Workspace", slug="test-workspace")
    db_session.add(workspace)
    await db_session.flush()

    # Admin User
    admin = User(
        workspace_id=workspace.id,
        email="admin@test.local",
        password_hash=get_password_hash("TestPassword123!"),
        full_name="Test Admin",
        role="ADMIN",
        is_active=True,
    )
    # Member User
    member = User(
        workspace_id=workspace.id,
        email="member@test.local",
        password_hash=get_password_hash("TestPassword123!"),
        full_name="Test Member",
        role="MEMBER",
        is_active=True,
    )
    db_session.add_all([admin, member])
    await db_session.flush()

    # Default pipeline
    lead_repo = LeadRepository(db_session)
    await lead_repo.get_or_create_default_pipeline(workspace.id)
    await db_session.commit()

    return {
        "workspace": workspace,
        "admin": admin,
        "member": member,
    }


@pytest.fixture
def admin_token(seed_data) -> str:
    admin = seed_data["admin"]
    return create_access_token(admin.id, admin.workspace_id, role="ADMIN")


@pytest.fixture
def member_token(seed_data) -> str:
    member = seed_data["member"]
    return create_access_token(member.id, member.workspace_id, role="MEMBER")


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
