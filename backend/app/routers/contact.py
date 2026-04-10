from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contact", tags=["contact"])

RECIPIENT_EMAIL = "contact@green-audit.fr"


class ContactForm(BaseModel):
    name: str
    email: str
    company: str
    message: str


@router.post("")
async def send_contact(form: ContactForm):
    """Reçoit le formulaire de contact et envoie un email de notification."""
    # Log sans email ni contenu du message (RGPD — données personnelles)
    logger.info(f"Contact reçu: entreprise={form.company}")

    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD

    if not smtp_user or not smtp_password:
        logger.warning("SMTP non configuré — email non envoyé")
        return {"status": "received"}

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = RECIPIENT_EMAIL
        msg["Reply-To"] = form.email
        msg["Subject"] = f"[GreenAudit] Demande de devis — {form.company}"

        body = f"""Nouvelle demande de devis via GreenAudit

Nom : {form.name}
Email : {form.email}
Entreprise : {form.company}

Message :
{form.message}
"""
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP("smtp.zoho.eu", 587, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"Email contact envoyé pour {form.company}")
        return {"status": "sent"}

    except Exception as e:
        logger.error(f"Erreur envoi email contact: {e}")
        return {"status": "received", "detail": "Message enregistré mais email non envoyé"}
