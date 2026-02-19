from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# ---------------------------------------------------------------------------
# SQLite compat : les modèles utilisent UUID PostgreSQL, on le remappe en
# String(36) quand le driver est SQLite (dev local sans PostgreSQL).
# ---------------------------------------------------------------------------
if settings.DATABASE_URL.startswith("sqlite"):
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    PG_UUID.impl = String(36)

engine = create_async_engine(settings.DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency FastAPI : fournit une session DB async."""
    async with async_session() as session:
        yield session
