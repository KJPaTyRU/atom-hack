from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from hmm.config import get_settings

engine = create_async_engine(get_settings().db.db_url, future=True, echo=False)
AsyncSessionMaker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncSession:
    async with AsyncSessionMaker() as session:
        yield session
