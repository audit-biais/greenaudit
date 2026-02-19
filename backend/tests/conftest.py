"""Fixtures pytest pour les tests GreenAudit."""

from __future__ import annotations

import uuid
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import String, event
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.main import app
from app.auth.jwt import create_access_token, hash_password
from app.models.partner import Partner
from app.models.audit import Audit
from app.models.claim import Claim

# ---------------------------------------------------------------------------
# SQLite compat : remplacer les UUID PostgreSQL par des String(36)
# ---------------------------------------------------------------------------
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

_orig_uuid_init = PG_UUID.__init__


def _patched_uuid_init(self, as_uuid=False):
    _orig_uuid_init(self, as_uuid=as_uuid)


PG_UUID.__init__ = _patched_uuid_init
PG_UUID.impl = String(36)


# ---------------------------------------------------------------------------
# Engine de test : SQLite async en mémoire
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(autouse=True)
async def setup_database():
    """
    Crée les tables, puis partage UNE connexion + transaction entre
    la fixture db_session et l'API (via dependency override).
    Rollback à la fin pour isoler chaque test.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Ouvrir une connexion unique pour tout le test
    conn: AsyncConnection = await test_engine.connect()
    trans = await conn.begin()

    # Session qui utilise cette connexion (partagée)
    session_factory = async_sessionmaker(
        bind=conn, class_=AsyncSession, expire_on_commit=False
    )

    # Override la dependency FastAPI pour utiliser la même session
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    # Stocker la factory pour la fixture db_session
    setup_database._session_factory = session_factory

    yield

    await trans.rollback()
    await conn.close()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Session DB de test — partage la même connexion que l'API."""
    factory = setup_database._session_factory
    async with factory() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Client HTTP async pour tester l'API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def partner(db_session: AsyncSession) -> Partner:
    """Crée un partenaire de test."""
    p = Partner(
        id=uuid.uuid4(),
        email="test@greenaudit.fr",
        password_hash=hash_password("testpass123"),
        company_name="Agence Test",
        brand_primary_color="#1B5E20",
        brand_secondary_color="#2E7D32",
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


@pytest.fixture
def auth_headers(partner: Partner) -> dict:
    """Headers Authorization avec JWT valide."""
    token = create_access_token(str(partner.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def audit(db_session: AsyncSession, partner: Partner) -> Audit:
    """Crée un audit draft de test."""
    a = Audit(
        id=uuid.uuid4(),
        partner_id=partner.id,
        company_name="Entreprise Test",
        sector="e-commerce",
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)
    return a


@pytest.fixture
async def claim(db_session: AsyncSession, audit: Audit) -> Claim:
    """Crée une claim de test basique (terme générique, pas de preuve)."""
    c = Claim(
        id=uuid.uuid4(),
        audit_id=audit.id,
        claim_text="Notre produit est écologique et respectueux de l'environnement",
        support_type="web",
        scope="produit",
        has_proof=False,
        has_label=False,
        is_future_commitment=False,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c
