# security/jwt/create_access_token.py
from datetime import datetime, timedelta, timezone
from jose import jwt
from core.settings import settings

def create_access_token(sub: str, role: str = "user", minutes: int | None = None) -> str:
    """
    Create a signed JWT access token.
    - sub: the user ID or email
    - role: user role ("user" or "admin")
    - minutes: optional expiration override
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": sub,
        "role": role,
        "exp": expire
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    return token
