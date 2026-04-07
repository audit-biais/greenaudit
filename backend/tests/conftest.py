"""Fixtures pytest pour les tests GreenAudit — architecture User + Organization."""

from __future__ import annotations

import os
import uuid
from typing import AsyncGenerator

# Définir les variables d'env AVANT tout import de l'app
os.environ.setdefault("SECRET_KEY", "a-very-long-secret-key-for-testing-purposes-1234567")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("SUPERADMIN_EMAIL", "superadmin@test.com")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.main import app
from app.auth.jwt import create_access_token, hash_password
from app.models.audit import Audit
from app.models.claim import Claim
from app.models.organization import Organization
from app.models.user import User

# ---------------------------------------------------------------------------
# SQLite compat : remplacer les UUID PostgreSQL par des String(36)
# ---------------------------------------------------------------------------
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

    conn: AsyncConnection = await test_engine.connect()
    trans = await conn.begin()

    session_factory = async_sessionmaker(
        bind=conn, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    setup_database._session_factory = session_factory

    yield

    await trans.rollback()
    await conn.close()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Fixtures DB / HTTP
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


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

async def _make_user_with_org(
    db: AsyncSession,
    email: str,
    password: str = "testpass123!",
    plan: str = "pro",
) -> User:
    """Crée une Organisation + User liés (pro par défaut pour accéder à toutes les features)."""
    org = Organization(
        id=uuid.uuid4(),
        name=f"Org {email}",
        contact_email=email,
        subscription_plan=plan,
        subscription_status="active",
        audits_limit=15 if plan == "pro" else 1,
    )
    db.add(org)
    await db.flush()

    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password(password),
        company_name=f"Entreprise {email}",
        organization_id=org.id,
        subscription_plan=plan,
        subscription_status="active",
        audits_limit=15 if plan == "pro" else 1,
        is_active=True,
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _token_for(user: User) -> str:
    """Génère un JWT valide pour un utilisateur."""
    return create_access_token({"sub": user.email, "user_id": str(user.id)})


# ---------------------------------------------------------------------------
# Fixtures utilisateurs (deux tenants distincts)
# ---------------------------------------------------------------------------

@pytest.fixture
async def user_a(db_session: AsyncSession) -> User:
    return await _make_user_with_org(db_session, "user_a@test.com")


@pytest.fixture
async def user_b(db_session: AsyncSession) -> User:
    return await _make_user_with_org(db_session, "user_b@test.com")


@pytest.fixture
def headers_a(user_a: User) -> dict:
    return {"Authorization": f"Bearer {_token_for(user_a)}"}


@pytest.fixture
def headers_b(user_b: User) -> dict:
    return {"Authorization": f"Bearer {_token_for(user_b)}"}


# ---------------------------------------------------------------------------
# Fixtures audit / claim (appartiennent à user_a / org_a)
# ---------------------------------------------------------------------------

@pytest.fixture
async def audit_a(db_session: AsyncSession, user_a: User) -> Audit:
    """Audit draft appartenant à l'organisation de user_a."""
    a = Audit(
        id=uuid.uuid4(),
        organization_id=user_a.organization_id,
        company_name="Entreprise A",
        sector="e-commerce",
        created_by_user_id=user_a.id,
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)
    return a


@pytest.fixture
async def claim_a(db_session: AsyncSession, audit_a: Audit) -> Claim:
    """Claim appartenant à l'audit de user_a."""
    c = Claim(
        id=uuid.uuid4(),
        audit_id=audit_a.id,
        claim_text="Notre produit est écologique",
        support_type="web",
        scope="produit",
        has_proof=False,
        proof_type="aucune",
        has_label=False,
        is_future_commitment=False,
        has_independent_verification=False,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c
