from __future__ import annotations

from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings

_UNSAFE_SECRETS = {
    "change-me-in-production",
    "changeme",
    "secret",
    "dev-secret-key-change-in-prod",
    "dev-secret",
    "",
}


class Settings(BaseSettings):
    """Configuration de l'application GreenAudit."""

    # Base de données — obligatoire, pas de fallback silencieux
    DATABASE_URL: str

    # JWT — obligatoire, pas de fallback silencieux
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # CORS — stocké comme string, parsé dans main.py
    CORS_ORIGINS: str = "http://localhost:5173"

    # Stockage PDF
    PDF_STORAGE_PATH: str = "./reports"

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRO_PRICE_ID: Optional[str] = None  # Price ID du plan Pro 2990€/mois
    FRONTEND_URL: str = "https://green-audit.fr"

    # Claude API (monitoring continu)
    ANTHROPIC_API_KEY: Optional[str] = None

    # Firecrawl (scraping pages web)
    FIRECRAWL_API_KEY: Optional[str] = None

    # Super admin (email qui déclenche l'activation automatique du flag is_superadmin)
    SUPERADMIN_EMAIL: Optional[str] = None

    # SMTP (formulaire de contact + accès client)
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Brevo API (email transactionnel)
    BREVO_API_KEY: Optional[str] = None

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if v.lower() in _UNSAFE_SECRETS or len(v) < 32:
            raise ValueError(
                "SECRET_KEY est trop faible ou utilise une valeur par défaut. "
                "Générez une clé sécurisée : python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def database_url_must_not_be_default(cls, v: str) -> str:
        if "user:pass@localhost" in v:
            raise ValueError(
                "DATABASE_URL utilise la valeur par défaut. "
                "Configurez une vraie URL de base de données."
            )
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
