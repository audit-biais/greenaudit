from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_admin_user
from app.auth.jwt import hash_password
from app.database import get_db
from app.models.audit import Audit
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import (
    InviteRequest,
    OrgResponse,
    OrgSettings,
    OrgUserResponse,
)

router = APIRouter(prefix="/api/organizations", tags=["organizations"])

MAX_LOGO_SIZE = 2 * 1024 * 1024  # 2 Mo



@router.get("/me", response_model=OrgResponse)
async def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retourne les détails de l'organisation de l'utilisateur."""
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Aucune organisation")

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    return await _org_to_response(org, db)


@router.put("/settings")
async def update_org_settings(
    data: OrgSettings,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Met à jour les paramètres de l'organisation (admin seulement)."""
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    await db.commit()
    await db.refresh(org)

    return {
        "status": "success",
        "message": "Paramètres mis à jour",
        "organization": await _org_to_response(org, db),
    }


@router.post("/logo")
async def upload_logo(
    logo: UploadFile = File(...),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload le logo de l'organisation (admin seulement). PNG ou JPEG, max 2 Mo."""
    if logo.content_type not in ("image/png", "image/jpeg"):
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez PNG ou JPEG.")

    contents = await logo.read()
    if len(contents) > MAX_LOGO_SIZE:
        raise HTTPException(status_code=413, detail="Logo trop volumineux. Taille maximale : 2 Mo")

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    org.logo_data = contents
    org.logo_content_type = logo.content_type
    await db.commit()

    return {"status": "success", "message": "Logo mis à jour"}


@router.get("/logo/{org_id}")
async def get_logo(org_id: str, db: AsyncSession = Depends(get_db)) -> Response:
    """Sert le logo d'une organisation (route publique pour le PDF)."""
    from uuid import UUID
    try:
        org_uuid = UUID(org_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")

    result = await db.execute(select(Organization).where(Organization.id == org_uuid))
    org = result.scalar_one_or_none()

    if not org or not org.logo_data:
        raise HTTPException(status_code=404, detail="Aucun logo trouvé")

    return Response(
        content=org.logo_data,
        media_type=org.logo_content_type or "image/png",
    )


@router.get("/users")
async def list_org_users(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Liste les utilisateurs de l'organisation (admin seulement)."""
    result = await db.execute(
        select(User).where(User.organization_id == current_user.organization_id)
    )
    users = list(result.scalars().all())

    return {
        "users": [OrgUserResponse.model_validate(u).model_dump() for u in users]
    }


@router.post("/invite")
async def invite_user(
    data: InviteRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Invite un utilisateur par email (admin seulement)."""
    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalar_one_or_none()

    if existing:
        if existing.organization_id:
            raise HTTPException(
                status_code=400,
                detail="Cet utilisateur appartient déjà à une organisation",
            )
        existing.organization_id = current_user.organization_id
        existing.role = "member"
        await db.commit()
        return {"status": "success", "message": f"{data.email} ajouté à l'organisation"}

    # Créer un utilisateur inactif (sera activé au signup)
    new_user = User(
        email=data.email,
        company_name=current_user.company_name,
        hashed_password=hash_password("invited-temp-password"),
        is_active=False,
        organization_id=current_user.organization_id,
        role="member",
    )
    db.add(new_user)
    await db.commit()

    return {
        "status": "success",
        "message": f"Invitation envoyée à {data.email}. L'utilisateur pourra s'inscrire avec cet email.",
    }


@router.delete("/users/{user_id}")
async def remove_user(
    user_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retire un utilisateur de l'organisation (admin seulement)."""
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalide")

    if user_uuid == current_user.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas vous retirer vous-même")

    result = await db.execute(
        select(User).where(
            User.id == user_uuid,
            User.organization_id == current_user.organization_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable dans votre organisation")

    user.organization_id = None
    user.role = "member"
    await db.commit()

    return {"status": "success", "message": f"{user.email} retiré de l'organisation"}


@router.delete("/me")
async def delete_my_organization(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Supprime l'organisation et tous ses utilisateurs (Art. 17 RGPD — droit à l'effacement). Admin uniquement."""
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Aucune organisation trouvée")

    org_id = current_user.organization_id

    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    # Détacher tous les utilisateurs de l'organisation (avant suppression)
    users_result = await db.execute(
        select(User).where(User.organization_id == org_id)
    )
    users = list(users_result.scalars().all())
    for u in users:
        u.organization_id = None
        u.role = "member"

    await db.flush()

    # Supprimer les audits via ORM pour déclencher les cascades (claims, evidence, etc.)
    audits_result = await db.execute(
        select(Audit).where(Audit.organization_id == org_id)
    )
    for audit in audits_result.scalars().all():
        await db.delete(audit)

    await db.flush()
    await db.delete(org)
    await db.commit()

    return {"status": "success", "message": "Compte et données supprimés conformément au RGPD (Art. 17)"}


async def _org_to_response(org: Organization, db: AsyncSession) -> dict:
    result = await db.execute(
        select(User).where(User.organization_id == org.id)
    )
    users_count = len(list(result.scalars().all()))

    return OrgResponse(
        id=org.id,
        name=org.name,
        contact_email=org.contact_email,
        contact_name=org.contact_name,
        contact_phone=org.contact_phone,
        brand_primary_color=org.brand_primary_color,
        brand_secondary_color=org.brand_secondary_color,
        has_logo=org.logo_data is not None,
        subscription_plan=org.subscription_plan,
        subscription_status=org.subscription_status,
        audits_this_month=org.audits_this_month,
        audits_limit=org.audits_limit,
        created_at=org.created_at,
        users_count=users_count,
    ).model_dump()
