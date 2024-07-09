from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase, MappedAsDataclass):
    pass


DATABASE_URL = settings.DATABASE_URI

async_engine = create_async_engine(DATABASE_URL, echo=False, future=True)
local_session = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def async_get_db() -> AsyncSession:
    async_session = local_session
    async with async_session() as db:
        yield db