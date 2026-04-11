from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.auth.dependencies import get_current_user, get_superadmin_user
from app.auth.jwt import hash_password
from app.database import get_db
from app.models.audit import Audit
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])

PLAN_LIMITS = {
    "starter": 1,
    "essentiel": 10,
    "pro": 9999,
    "enterprise": 9999,
}


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # "admin" ou "member"
    org_id: UUID


class SetPlanRequest(BaseModel):
    plan: str


@router.get("/overview")
async def get_overview(
    _: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Retourne toutes les organisations avec leurs membres et stats."""
    orgs_result = await db.execute(select(Organization).order_by(Organization.created_at.desc()))
    orgs = list(orgs_result.scalars().all())

    result = []
    for org in orgs:
        members_result = await db.execute(
            select(User).where(User.organization_id == org.id, User.is_active == True)
        )
        members = list(members_result.scalars().all())

        admin = next((u for u in members if u.role == "admin"), members[0] if members else None)

        audits_result = await db.execute(
            select(Audit).where(Audit.organization_id == org.id)
        )
        total_audits = len(list(audits_result.scalars().all()))

        result.append({
            "org_id": str(org.id),
            "org_name": org.name,
            "admin_email": admin.email if admin else org.contact_email,
            "plan": org.subscription_plan,
            "subscription_status": org.subscription_status,
            "audits_this_month": org.audits_this_month,
            "audits_limit": org.audits_limit,
            "total_audits": total_audits,
            "created_at": org.created_at.strftime("%d/%m/%Y") if org.created_at else "",
            "members": [
                {
                    "user_id": str(u.id),
                    "email": u.email,
                    "role": u.role or "member",
                    "audits_this_month": u.audits_this_month,
                }
                for u in members
            ],
        })

    # Users sans org
    solo_result = await db.execute(
        select(User).where(User.organization_id == None, User.is_superadmin == False)
    )
    solo_users = list(solo_result.scalars().all())
    if solo_users:
        result.append({
            "org_id": None,
            "org_name": "— Sans organisation —",
            "admin_email": None,
            "plan": "starter",
            "subscription_status": "inactive",
            "audits_this_month": sum(u.audits_this_month for u in solo_users),
            "audits_limit": 0,
            "total_audits": 0,
            "created_at": "",
            "members": [
                {
                    "user_id": str(u.id),
                    "email": u.email,
                    "role": u.role or "member",
                    "audits_this_month": u.audits_this_month,
                }
                for u in solo_users
            ],
        })

    return result


@router.patch("/orgs/{org_id}/plan")
async def set_org_plan(
    org_id: UUID,
    data: SetPlanRequest,
    _: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Force un plan sur une organisation (sans passer par Stripe)."""
    if data.plan not in PLAN_LIMITS:
        raise HTTPException(status_code=400, detail=f"Plan invalide : {data.plan}")

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    org.subscription_plan = data.plan
    org.subscription_status = "active" if data.plan != "starter" else "inactive"
    org.audits_limit = PLAN_LIMITS[data.plan]
    await db.commit()
    return {"message": f"Plan mis à jour : {data.plan}"}


@router.post("/users")
async def create_user(
    data: CreateUserRequest,
    _: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Crée un compte admin ou collaborateur pour une organisation."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    if data.role not in ("admin", "member"):
        raise HTTPException(status_code=400, detail="Role invalide")

    org_result = await db.execute(select(Organization).where(Organization.id == data.org_id))
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")

    new_user = User(
        email=data.email,
        company_name=org.name,
        hashed_password=hash_password(data.password),
        is_active=True,
        organization_id=data.org_id,
        role=data.role,
    )
    db.add(new_user)
    await db.commit()
    return {"message": f"Compte {data.role} créé : {data.email}"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Supprime un utilisateur (et son org si elle devient vide)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Impossible de supprimer votre propre compte")

    org_id = user.organization_id
    await db.delete(user)
    await db.flush()

    # Si l'org est vide après suppression, la supprimer aussi
    if org_id:
        remaining = await db.execute(select(User).where(User.organization_id == org_id))
        if not remaining.scalars().first():
            org_result = await db.execute(select(Organization).where(Organization.id == org_id))
            org = org_result.scalar_one_or_none()
            if org:
                await db.delete(org)

    await db.commit()
    return {"message": "Compte supprimé"}
