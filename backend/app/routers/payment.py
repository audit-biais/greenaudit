from __future__ import annotations

import stripe
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_pro
from app.config import settings
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/api/payment", tags=["payment"])


def _init_stripe() -> None:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe non configuré")
    stripe.api_key = settings.STRIPE_SECRET_KEY


async def _get_org(user: User, db: AsyncSession) -> Organization:
    result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation introuvable")
    return org


@router.post("/create-checkout")
async def create_checkout(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Crée une session Stripe Checkout pour le plan Pro (2 990€/mois)."""
    if not user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous devez appartenir à une organisation",
        )
    if not settings.STRIPE_PRO_PRICE_ID:
        raise HTTPException(status_code=503, detail="Plan Pro non configuré")

    _init_stripe()
    org = await _get_org(user, db)

    if org.subscription_plan == "pro":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous êtes déjà sur le plan Pro",
        )

    params: dict = dict(
        mode="subscription",
        line_items=[{"price": settings.STRIPE_PRO_PRICE_ID, "quantity": 1}],
        success_url=f"{settings.FRONTEND_URL}/payment/success",
        cancel_url=f"{settings.FRONTEND_URL}/settings",
        metadata={"organization_id": str(org.id)},
        subscription_data={"metadata": {"organization_id": str(org.id)}},
    )

    if org.stripe_customer_id:
        params["customer"] = org.stripe_customer_id
    else:
        params["customer_email"] = user.email

    session = stripe.checkout.Session.create(**params)
    return {"checkout_url": session.url}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Webhook Stripe — met à jour le plan de l'organisation."""
    if not settings.STRIPE_WEBHOOK_SECRET or not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe non configuré")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Signature Stripe invalide")

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        org_id = (session_obj.get("metadata") or {}).get("organization_id")
        if org_id:
            try:
                org_uuid = UUID(org_id)
            except ValueError:
                return {"received": True}
            result = await db.execute(
                select(Organization).where(Organization.id == org_uuid)
            )
            org = result.scalar_one_or_none()
            if org:
                org.subscription_plan = "pro"
                org.subscription_status = "active"
                org.audits_limit = 15
                org.audits_this_month = 0
                org.audits_reset_month = None
                org.stripe_customer_id = session_obj.get("customer")
                org.stripe_subscription_id = session_obj.get("subscription")
                await db.commit()

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.paused"):
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        if customer_id:
            result = await db.execute(
                select(Organization).where(Organization.stripe_customer_id == customer_id)
            )
            org = result.scalar_one_or_none()
            if org:
                org.subscription_plan = "starter"
                org.subscription_status = "inactive"
                org.audits_limit = 1
                org.stripe_subscription_id = None
                await db.commit()

    return {"received": True}


@router.post("/portal")
async def billing_portal(
    user: User = Depends(require_pro),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Crée une session Stripe Billing Portal pour gérer l'abonnement."""
    _init_stripe()
    org = await _get_org(user, db)

    if not org.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun abonnement Stripe actif",
        )

    portal_session = stripe.billing_portal.Session.create(
        customer=org.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/settings",
    )
    return {"portal_url": portal_session.url}
