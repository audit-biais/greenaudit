from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_partner
from app.database import get_db
from app.models.partner import Partner
from app.schemas.partner import (
    PartnerBrandingUpdate,
    PartnerResponse,
    PartnerUpdate,
)

router = APIRouter(prefix="/api/partners", tags=["partners"])


@router.get("/me", response_model=PartnerResponse)
async def get_partner_profile(
    partner: Partner = Depends(get_current_partner),
) -> Partner:
    """Infos du partenaire courant."""
    return partner


@router.put("/me", response_model=PartnerResponse)
async def update_partner_profile(
    data: PartnerUpdate,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> Partner:
    """Modifier le profil du partenaire."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(partner, field, value)
    await db.commit()
    await db.refresh(partner)
    return partner


@router.put("/me/branding", response_model=PartnerResponse)
async def update_partner_branding(
    data: PartnerBrandingUpdate,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> Partner:
    """Modifier le branding white-label (logo + couleurs)."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(partner, field, value)
    await db.commit()
    await db.refresh(partner)
    return partner
