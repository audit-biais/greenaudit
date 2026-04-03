from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy import text

from app.config import settings
from app.database import engine, Base
from app.routers import auth, partners, audits, claims, reports
from app.routers import monitoring, contact, organizations

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Crée les tables au démarrage et démarre le scheduler de monitoring."""
    # Migration one-shot : si la table audits a encore partner_id, on recrée tout
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'audits' AND column_name = 'partner_id'
        """))
        if result.fetchone():
            logger.info("Migration: ancien schéma détecté (partner_id), suppression des tables pour recréation")
            await conn.execute(text("DROP TABLE IF EXISTS monitoring_alerts CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS monitoring_configs CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS claim_results CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS claims CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS audits CASCADE"))

    # Créer les tables (dev only — en prod, utiliser Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler de debug temporaire — à retirer en prod."""
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__, "trace": traceback.format_exc()},
    )


app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(partners.router)
app.include_router(audits.router)
app.include_router(claims.router)
app.include_router(reports.router)
app.include_router(monitoring.router)
app.include_router(contact.router)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}
