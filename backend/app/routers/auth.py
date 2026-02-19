from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_partner
from app.auth.jwt import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.partner import Partner
from app.schemas.partner import (
    PartnerLogin,
    PartnerRegister,
    PartnerResponse,
    TokenResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: PartnerRegister,
    db: AsyncSession = Depends(get_db),
) -> Partner:
    """Inscription d'un nouveau partenaire."""
    # Vérifier unicité email
    result = await db.execute(select(Partner).where(Partner.email == data.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà",
        )

    partner = Partner(
        email=data.email,
        password_hash=hash_password(data.password),
        company_name=data.company_name,
        contact_name=data.contact_name,
        contact_phone=data.contact_phone,
    )
    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return partner


@router.post("/login", response_model=TokenResponse)
async def login(
    data: PartnerLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Connexion partenaire → JWT."""
    result = await db.execute(select(Partner).where(Partner.email == data.email))
    partner = result.scalar_one_or_none()

    if partner is None or not verify_password(data.password, partner.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if not partner.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé",
        )

    token = create_access_token(str(partner.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=PartnerResponse)
async def get_me(
    partner: Partner = Depends(get_current_partner),
) -> Partner:
    """Profil du partenaire courant."""
    return partner
