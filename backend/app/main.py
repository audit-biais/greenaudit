from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

import sqlalchemy as sa
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import auth, partners, audits, claims, reports
from app.routers import monitoring, contact, organizations, admin, evidence, payment

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Crée les tables au démarrage et démarre le scheduler de monitoring."""
    # Créer les tables (dev only — en prod, utiliser Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Migrations manuelles idempotentes (ADD COLUMN IF NOT EXISTS)
    async with engine.begin() as conn:
        await conn.execute(sa.text(
            "ALTER TABLE audits ADD COLUMN IF NOT EXISTS country VARCHAR(5) NOT NULL DEFAULT 'fr'"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE audits ADD COLUMN IF NOT EXISTS rules_version VARCHAR(20)"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE evidence_files ADD COLUMN IF NOT EXISTS document_type VARCHAR(50) NOT NULL DEFAULT 'autre'"
        ))
        # Renommer plan 'free' → 'starter' pour les orgs existantes
        await conn.execute(sa.text(
            "UPDATE organizations SET subscription_plan = 'starter' WHERE subscription_plan = 'free'"
        ))
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

cors_origins = [s.strip() for s in settings.CORS_ORIGINS.split(",") if s.strip()]

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
app.include_router(partners.router)
app.include_router(audits.router)
app.include_router(claims.router)
app.include_router(reports.router)
app.include_router(evidence.router)
app.include_router(monitoring.router)
app.include_router(contact.router)
app.include_router(payment.router)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}
