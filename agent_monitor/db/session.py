from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from agent_monitor.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args=settings.database_connect_args,
    pool_pre_ping=True,  # Neon 会回收空闲连接，用前 ping 探测避免 "connection is closed"
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
