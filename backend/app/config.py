from __future__ import annotations

import json
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration de l'application GreenAudit."""

    # Base de données
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/greenaudit"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # CORS — stocké comme string, parsé dans main.py
    CORS_ORIGINS: str = "http://localhost:5173"

    # Stockage PDF
    PDF_STORAGE_PATH: str = "./reports"

    # Stripe (optionnel)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Claude API (monitoring continu)
    ANTHROPIC_API_KEY: Optional[str] = None


    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
