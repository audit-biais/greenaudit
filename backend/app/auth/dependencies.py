from __future__ import annotations

from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access_token
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extrait et valide le JWT, retourne l'utilisateur courant."""
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email: str = payload.get("sub", "")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé",
        )

    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Vérifie que l'utilisateur est admin de son organisation."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'appartenez à aucune organisation",
        )
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action réservée aux administrateurs",
        )
    return current_user


def get_superadmin_user(current_user: User = Depends(get_current_user)) -> User:
    """Vérifie que l'utilisateur est super admin."""
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé au super administrateur",
        )
    return current_user


async def check_audit_limit(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Vérifie si l'utilisateur peut encore faire des audits ce mois-ci.
    Utilise le pool org si l'utilisateur a une organisation, sinon user-level.
    """
    if current_user.is_superadmin:
        return current_user

    current_month = datetime.utcnow().strftime("%Y-%m")

    if current_user.organization_id:
        result = await db.execute(
            select(Organization).where(Organization.id == current_user.organization_id)
        )
        org = result.scalar_one_or_none()
        if org:
            if org.audits_reset_month != current_month:
                org.audits_this_month = 0
                org.audits_reset_month = current_month
                await db.commit()
            if org.audits_this_month >= org.audits_limit:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Limite d'audits atteinte ({org.audits_limit}/mois). L'admin doit upgrader le plan.",
                )
    else:
        if current_user.audits_reset_month != current_month:
            current_user.audits_this_month = 0
            current_user.audits_reset_month = current_month
            await db.commit()
        if current_user.audits_this_month >= current_user.audits_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Limite d'audits atteinte ({current_user.audits_limit}/mois). Passez à un plan supérieur.",
            )

    return current_user
