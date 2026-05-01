import asyncio
import logging
import smtplib
from concurrent.futures import ThreadPoolExecutor
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, oauth2_scheme
from app.auth.jwt import create_access_token, decode_access_token, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.limiter import limiter
from app.models.organization import Organization
from app.models.user import User
from app.schemas.user import OrgInfo, TokenResponse, UserResponse, UserSignup
from app.services.demo_audit import create_demo_audit

logger = logging.getLogger(__name__)


_email_executor = ThreadPoolExecutor(max_workers=2)


def _send_welcome_email_sync(to_email: str) -> None:
    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD
    if not smtp_user or not smtp_password:
        logger.warning("SMTP non configuré — email de bienvenue non envoyé")
        return
    msg = MIMEMultipart("alternative")
    msg["From"] = "GreenAudit <contact@green-audit.fr>"
    msg["To"] = to_email
    msg["Subject"] = "Bienvenue sur GreenAudit — votre premier audit vous attend"
    body = """\
Bonjour,

Votre compte GreenAudit est actif. Voici comment démarrer en 3 étapes :

1. Connectez-vous sur https://www.green-audit.fr
2. Cliquez sur "Analyse" pour scanner un site web ou "Nouvel audit" pour saisir des allégations manuellement
3. Téléchargez le rapport PDF de conformité EmpCo

Votre plan Starter inclut 1 audit complet. Pour des audits illimités, passez au plan Pro depuis Paramètres > Abonnement.

Une question ? Répondez directement à cet email ou contactez-nous sur https://www.green-audit.fr/contact

L'équipe GreenAudit
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))
    with smtplib.SMTP("smtp-relay.brevo.com", 587, timeout=15) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    logger.info(f"Email de bienvenue envoyé à {to_email}")


async def _send_welcome_email(to_email: str) -> None:
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            _email_executor,
            _send_welcome_email_sync,
            to_email,
        )
    except Exception as e:
        logger.error(f"Erreur email bienvenue ({to_email}): {e}")

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def signup(
    request: Request,
    data: UserSignup,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Inscription d'un nouvel utilisateur.

    Si l'email a été invité (user inactif avec org), on l'active.
    Sinon, on crée un nouveau user + une organisation automatiquement.
    """
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        # Flow invitation : user inactif avec org
        if not existing_user.is_active and existing_user.organization_id:
            existing_user.hashed_password = hash_password(data.password)
            existing_user.company_name = data.company_name
            existing_user.is_active = True
            await db.commit()
            await db.refresh(existing_user)
            return await _user_to_response(existing_user, db)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé",
        )

    # Créer l'utilisateur
    new_user = User(
        email=data.email,
        company_name=data.company_name,
        hashed_password=hash_password(data.password),
        subscription_plan="starter",
        audits_limit=1,
        role="admin",
    )
    db.add(new_user)
    await db.flush()

    # Auto-créer une organisation
    org = Organization(
        name=data.company_name,
        contact_email=data.email,
    )
    db.add(org)
    await db.flush()

    new_user.organization_id = org.id
    await db.commit()
    await db.refresh(new_user)

    await create_demo_audit(org.id, db)
    asyncio.create_task(_send_welcome_email(data.email))

    return await _user_to_response(new_user, db)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Connexion → JWT (7 jours)."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé",
        )

    # Activer le superadmin automatiquement si l'email correspond
    superadmin_email = settings.SUPERADMIN_EMAIL or ""
    if superadmin_email and user.email == superadmin_email and not user.is_superadmin:
        user.is_superadmin = True
        await db.commit()
        await db.refresh(user)

    token = create_access_token(data={"sub": user.email, "user_id": str(user.id)})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Profil de l'utilisateur connecté avec les données org."""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub", "")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )

    return await _user_to_response(user, db)


async def _user_to_response(user: User, db: AsyncSession) -> dict:
    """Construit la réponse user avec les données org."""
    org_info = None

    if user.organization_id:
        result = await db.execute(
            select(Organization).where(Organization.id == user.organization_id)
        )
        org = result.scalar_one_or_none()
        if org:
            org_info = OrgInfo(
                id=org.id,
                name=org.name,
                has_logo=org.logo_data is not None,
                brand_primary_color=org.brand_primary_color,
                brand_secondary_color=org.brand_secondary_color,
                subscription_plan=org.subscription_plan,
                subscription_status=org.subscription_status,
                audits_this_month=org.audits_this_month,
                audits_limit=org.audits_limit,
            )

            return UserResponse(
                id=user.id,
                email=user.email,
                company_name=user.company_name,
                role=user.role or "member",
                subscription_plan=org.subscription_plan,
                subscription_status=org.subscription_status,
                audits_this_month=org.audits_this_month,
                audits_limit=org.audits_limit,
                organization=org_info,
                is_superadmin=user.is_superadmin or False,
            ).model_dump()

    return UserResponse(
        id=user.id,
        email=user.email,
        company_name=user.company_name,
        role=user.role or "member",
        subscription_plan=user.subscription_plan,
        subscription_status=user.subscription_status,
        audits_this_month=user.audits_this_month,
        audits_limit=user.audits_limit,
        organization=None,
        is_superadmin=user.is_superadmin or False,
    ).model_dump()
