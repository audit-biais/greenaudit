from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

import sqlalchemy as sa
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.limiter import limiter
from app.utils.security_headers import SecurityHeadersMiddleware
from app.database import engine, Base
from app.models import client_access as _  # noqa: F401 — register ClientAccess with SQLAlchemy
from app.routers import auth, audits, claims, reports
from app.routers import monitoring, contact, organizations, admin, evidence, payment, members, share

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Crée les tables au démarrage et démarre le scheduler de monitoring."""
    # Créer les tables (dev only — en prod, utiliser Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Migrations manuelles idempotentes — SQLite ne supporte pas IF NOT EXISTS
    # dans ALTER TABLE, on attrape l'erreur "duplicate column" silencieusement.
    _ALTER_SQLS = [
        "ALTER TABLE audits ADD COLUMN country VARCHAR(5) NOT NULL DEFAULT 'fr'",
        "ALTER TABLE audits ADD COLUMN rules_version VARCHAR(20)",
        "ALTER TABLE evidence_files ADD COLUMN document_type VARCHAR(50) NOT NULL DEFAULT 'autre'",
        "ALTER TABLE claims ADD COLUMN is_corrected BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE claims ADD COLUMN corrected_at TIMESTAMPTZ",
        "ALTER TABLE claims ADD COLUMN is_false_positive BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE claims ADD COLUMN false_positive_reason VARCHAR(100)",
        "ALTER TABLE audits ADD COLUMN created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL",
        "ALTER TABLE audits ADD COLUMN pdf_sha256 VARCHAR(64)",
        "ALTER TABLE audits ADD COLUMN share_token_expires_at TIMESTAMPTZ",
        "ALTER TABLE claims ADD COLUMN regulatory_basis VARCHAR(50)",
        "ALTER TABLE claims ADD COLUMN regime VARCHAR(20)",
        "ALTER TABLE claims ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'À traiter'",
        "ALTER TABLE claims ADD COLUMN source_url VARCHAR(500)",
        "ALTER TABLE audits ADD COLUMN pdf_marque_url TEXT",
        "ALTER TABLE audits ADD COLUMN pdf_marque_sha256 VARCHAR(64)",
    ]
    async with engine.begin() as conn:
        for sql in _ALTER_SQLS:
            try:
                await conn.execute(sa.text(sql))
            except Exception:
                pass  # Colonne déjà existante
        # Renommer plan 'free' → 'starter' pour les orgs existantes
        try:
            await conn.execute(sa.text(
                "UPDATE organizations SET subscription_plan = 'starter' WHERE subscription_plan = 'free'"
            ))
        except Exception:
            pass
        # Table coffre-fort client (fallback si create_all ne l'a pas créée)
        try:
            await conn.execute(sa.text("""
                CREATE TABLE IF NOT EXISTS client_accesses (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    audit_id UUID NOT NULL UNIQUE REFERENCES audits(id) ON DELETE CASCADE,
                    token VARCHAR(200) NOT NULL UNIQUE,
                    client_email VARCHAR(255) NOT NULL,
                    validity_days INTEGER,
                    expires_at TIMESTAMPTZ,
                    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    last_opened_at TIMESTAMPTZ,
                    pdf_downloaded_at TIMESTAMPTZ,
                    zip_downloaded_at TIMESTAMPTZ
                )
            """))
        except Exception:
            pass  # Déjà créée par create_all ou syntaxe non supportée (SQLite)
    logger.info("Colonnes country + rules_version + document_type vérifiées/ajoutées")

    # Démarrer le scheduler APScheduler
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from app.services.monitoring_service import run_due_monitoring_checks

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_due_monitoring_checks,
        "interval",
        hours=1,
        id="monitoring_checks",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler de monitoring démarré (interval: 1h)")

    yield

    scheduler.shutdown(wait=False)
    await engine.dispose()


app = FastAPI(
    title="GreenAudit API",
    description="SaaS d'audit de conformité anti-greenwashing — Directive EmpCo (EU 2024/825)",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

cors_origins = [s.strip() for s in settings.CORS_ORIGINS.split(",") if s.strip()]

# IMPORTANT : les middlewares sont appliqués dans l'ordre inverse d'ajout.
# SecurityHeaders doit être en dernier (ajouté en premier) pour couvrir toutes les réponses,
# y compris celles générées par CORSMiddleware.
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://greenaudit.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(admin.router)
app.include_router(audits.router)
app.include_router(claims.router)
app.include_router(reports.router)
app.include_router(evidence.router)
app.include_router(monitoring.router)
app.include_router(contact.router)
app.include_router(payment.router)
app.include_router(members.router)
app.include_router(share.router)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}
