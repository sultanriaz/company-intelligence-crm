from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Base declarative class
Base = declarative_base()

# Configure Async Engine
is_sqlite = "sqlite" in settings.DATABASE_URL

async_engine_args = {
    "echo": settings.DB_ECHO,
    "future": True,
}
if is_sqlite:
    async_engine_args.update({
        "connect_args": {"timeout": 30.0, "check_same_thread": False},
    })
else:
    async_engine_args.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
    })

async_engine = create_async_engine(settings.DATABASE_URL, **async_engine_args)

if is_sqlite:
    from sqlalchemy import event

    @event.listens_for(async_engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Configure Sync Engine (for Alembic, synchronous Celery tasks, or migrations)
sync_engine_args = {"echo": settings.DB_ECHO}
if "sqlite" in settings.SYNC_DATABASE_URL:
    sync_engine_args.update({
        "connect_args": {"timeout": 30.0, "check_same_thread": False},
    })
else:
    sync_engine_args.update({
        "pool_size": 10,
        "max_overflow": 5,
        "pool_pre_ping": True,
    })

sync_engine = create_engine(settings.SYNC_DATABASE_URL, **sync_engine_args)

if "sqlite" in settings.SYNC_DATABASE_URL:
    from sqlalchemy import event

    @event.listens_for(sync_engine, "connect")
    def set_sync_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables in the database (useful for test and local sqlite dev)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
