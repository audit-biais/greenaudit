from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def get_user_or_ip(request: Request) -> str:
    """
    Clé de rate limit : user_id extrait du JWT si présent, sinon IP.
    Utilisé pour les endpoints coûteux (analyze, scan) afin de limiter
    par partenaire et non par IP (plusieurs utilisateurs peuvent partager la même IP).
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        try:
            from app.auth.jwt import decode_access_token
            payload = decode_access_token(token)
            if payload and payload.get("user_id"):
                return f"user:{payload['user_id']}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=get_remote_address)
