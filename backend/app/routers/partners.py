from __future__ import annotations

# Ce fichier est conservé pour rétrocompatibilité.
# La gestion du profil et du branding se fait maintenant via /api/organizations.
# Les routes /api/partners/me sont redirigées vers les données User + Organization.

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_admin_user, get_current_user
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.routers.organizations import _org_to_response
from sqlalchemy import select

router = APIRouter(prefix="/api/partners", tags=["partners"])


@router.get("/me")
async def get_partner_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Profil partenaire (organisation courante)."""
    if not current_user.organization_id:
        return {"id": str(current_user.id), "company_name": current_user.company_name, "email": current_user.email}

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        return {"id": str(current_user.id), "company_name": current_user.company_name, "email": current_user.email}

    return await _org_to_response(org, db)


@router.put("/me/branding")
async def update_branding(
    data: dict,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Modifier le branding (couleurs). Utiliser /api/organizations/logo pour le logo."""
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    if "brand_primary_color" in data:
        org.brand_primary_color = data["brand_primary_color"]
    if "brand_secondary_color" in data:
        org.brand_secondary_color = data["brand_secondary_color"]

    await db.commit()
    await db.refresh(org)
    return await _org_to_response(org, db)
