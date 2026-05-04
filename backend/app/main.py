from __future__ import annotations

import asyncio
import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import sentry_sdk

from app.config import settings
from app.limiter import limiter

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
from app.utils.security_headers import SecurityHeadersMiddleware
from app.database import engine
from app.routers import auth, audits, claims, reports
from app.routers import monitoring, contact, organizations, admin, evidence, payment, members, share

logger = logging.getLogger(__name__)


async def _run_migrations() -> None:
    """Lance alembic upgrade head dans un thread pour ne pas bloquer la boucle async."""
    def _upgrade() -> None:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Alembic migration failed:\n{result.stderr}")
        if result.stdout:
            logger.info("Alembic: %s", result.stdout.strip())

    await asyncio.to_thread(_upgrade)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lance les migrations Alembic au démarrage et démarre le scheduler de monitoring."""
    await _run_migrations()
    logger.info("Migrations Alembic appliquées")

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
