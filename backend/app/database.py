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

# Railway fournit postgresql:// mais asyncpg a besoin de postgresql+asyncpg://
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(db_url, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency FastAPI : fournit une session DB async."""
    async with async_session() as session:
        yield session
