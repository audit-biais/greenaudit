from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.jwt import hash_password
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/api/organizations", tags=["members"])

MEMBER_LIMITS = {
    "starter": 1,
    "free": 1,
    "pro": 10,
    "enterprise": None,  # illimité
}


class InviteMemberRequest(BaseModel):
    email: str
    password: str
    role: str = "member"


def _require_admin(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Réservé aux administrateurs de l'organisation",
        )


@router.get("/members")
async def list_members(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    result = await db.execute(
        select(User)
        .where(User.organization_id == user.organization_id, User.is_active == True)
        .order_by(User.created_at)
    )
    members = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "email": m.email,
            "company_name": m.company_name,
            "role": m.role or "member",
            "created_at": m.created_at.isoformat(),
            "is_self": m.id == user.id,
        }
        for m in members
    ]


@router.post("/members", status_code=status.HTTP_201_CREATED)
async def invite_member(
    data: InviteMemberRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(user)

    org_result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = org_result.scalar_one_or_none()
    plan = org.subscription_plan if org else "starter"

    limit = MEMBER_LIMITS.get(plan, 1)

    count_result = await db.execute(
        select(func.count()).where(
            User.organization_id == user.organization_id,
            User.is_active == True,
        )
    )
    current_count = count_result.scalar() or 0

    if limit is not None and current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limite de {limit} membres atteinte pour le plan {plan.capitalize()}.",
        )

    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé.",
        )

    new_member = User(
        email=data.email,
        company_name=user.company_name,
        hashed_password=hash_password(data.password),
        organization_id=user.organization_id,
        role=data.role if data.role in ("admin", "member") else "member",
        is_active=True,
        subscription_plan="starter",
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    return {
        "id": str(new_member.id),
        "email": new_member.email,
        "role": new_member.role,
        "created_at": new_member.created_at.isoformat(),
        "is_self": False,
    }


@router.delete("/members/{member_id}", status_code=status.HTTP_200_OK)
async def remove_member(
    member_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(user)

    if member_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas vous supprimer vous-même.",
        )

    result = await db.execute(
        select(User).where(
            User.id == member_id,
            User.organization_id == user.organization_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membre introuvable.",
        )

    await db.delete(member)
    await db.commit()
    return {"status": "ok"}
