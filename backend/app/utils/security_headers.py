from __future__ import annotations

from typing import Callable

_SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"strict-transport-security", b"max-age=31536000; includeSubDomains"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"content-security-policy", b"default-src 'none'"),
    (b"x-xss-protection", b"0"),
]


class SecurityHeadersMiddleware:
    """
    Middleware ASGI pur (pas BaseHTTPMiddleware) qui ajoute les headers
    de sécurité HTTP sur toutes les réponses.

    Implémenté en ASGI raw pour éviter les incompatibilités de BaseHTTPMiddleware
    avec les streaming responses et certaines versions de Starlette.

    Headers ajoutés :
    - X-Content-Type-Options: nosniff         → empêche le MIME-sniffing
    - X-Frame-Options: DENY                   → empêche le clickjacking
    - Strict-Transport-Security               → force HTTPS 1 an
    - Referrer-Policy                         → ne transmet que l'origine
    - Content-Security-Policy: default-src 'none' → API pure, rien à charger
    - X-XSS-Protection: 0                    → désactive le filtre XSS cassé
    """

    def __init__(self, app: Callable) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                existing = list(message.get("headers", []))
                message = {**message, "headers": existing + _SECURITY_HEADERS}
            await send(message)

        await self.app(scope, receive, send_with_security_headers)
