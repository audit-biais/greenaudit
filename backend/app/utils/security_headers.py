from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Ajoute les headers de sécurité HTTP sur toutes les réponses.

    - X-Content-Type-Options : empêche le MIME-sniffing (ex : un JSON servi
      comme HTML interprété par le navigateur).
    - X-Frame-Options : empêche l'intégration dans une iframe (clickjacking).
    - Strict-Transport-Security : force HTTPS pendant 1 an, y compris sous-domaines.
    - Referrer-Policy : ne transmet que l'origine dans le header Referer.
    - Content-Security-Policy : API pure → aucune ressource à charger depuis
      le navigateur, on bloque tout par défaut.
    - X-XSS-Protection: 0 : désactive le filtre XSS natif des vieux navigateurs
      (il crée plus de failles qu'il n'en corrige sur les navigateurs modernes).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'none'"
        response.headers["X-XSS-Protection"] = "0"
        return response
