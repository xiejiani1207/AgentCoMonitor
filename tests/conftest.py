import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from agent_monitor.config import settings


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(settings.database_url, echo=False)
    test_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        from agent_monitor.db.session import Base
        await conn.run_sync(Base.metadata.create_all)

    async with test_session() as session:
        yield session

    async with engine.begin() as conn:
        from agent_monitor.db.session import Base
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
