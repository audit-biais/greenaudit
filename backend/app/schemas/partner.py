from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- Request schemas ---

class PartnerRegister(BaseModel):
    """Inscription d'un nouveau partenaire."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(min_length=1, max_length=255)
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None


class PartnerLogin(BaseModel):
    """Connexion partenaire."""
    email: EmailStr
    password: str


class PartnerUpdate(BaseModel):
    """Mise à jour du profil partenaire."""
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None


class PartnerBrandingUpdate(BaseModel):
    """Mise à jour du branding white-label."""
    logo_url: Optional[str] = None
    brand_primary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    brand_secondary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


# --- Response schemas ---

class PartnerResponse(BaseModel):
    """Réponse partenaire (sans password_hash)."""
    id: UUID
    email: str
    company_name: str
    logo_url: Optional[str] = None
    brand_primary_color: str
    brand_secondary_color: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Réponse JWT après login."""
    access_token: str
    token_type: str = "bearer"
