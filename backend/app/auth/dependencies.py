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


async def require_pro(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Vérifie que l'organisation est sur plan Pro ou Enterprise."""
    if current_user.is_superadmin:
        return current_user

    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="upgrade_required",
        )

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org or org.subscription_plan not in ("partner", "pro", "enterprise"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="upgrade_required",
        )
    return current_user


async def check_audit_limit(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Vérifie si l'organisation peut créer un nouvel audit selon son plan.
    - starter : 1 audit unique one-shot (jamais réinitialisé)
    - pro     : 15 audits/mois, reset le 1er du mois
    - enterprise : illimité
    """
    if current_user.is_superadmin:
        return current_user

    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous devez appartenir à une organisation pour créer un audit",
        )

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organisation introuvable",
        )

    plan = org.subscription_plan

    # Enterprise : illimité
    if plan == "enterprise":
        return current_user

    # Partner : 5 audits/mois avec reset mensuel
    if plan == "partner":
        current_month = datetime.utcnow().strftime("%Y-%m")
        if org.audits_reset_month != current_month:
            org.audits_this_month = 0
            org.audits_reset_month = current_month
            await db.commit()
        if org.audits_this_month >= 5:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Limite de 5 audits/mois atteinte. Contactez-nous pour en ajouter.",
            )
        return current_user

    # Pro : 15 audits/mois avec reset mensuel
    if plan == "pro":
        current_month = datetime.utcnow().strftime("%Y-%m")
        if org.audits_reset_month != current_month:
            org.audits_this_month = 0
            org.audits_reset_month = current_month
            await db.commit()
        if org.audits_this_month >= 15:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Limite de 15 audits/mois atteinte. Contactez-nous pour en ajouter.",
            )
        return current_user

    # Starter (ou 'free') : 1 audit unique one-shot
    if org.audits_this_month >= 1:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="upgrade_required",
        )
    return current_user
