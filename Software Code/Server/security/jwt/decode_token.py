# security/jwt/decode_token.py
from jose import jwt, JWTError
from core.settings import settings

def decode_token(token: str) -> dict | None:
    """
    Decode and verify a JWT token.
    Returns payload dict if valid, else None.
    """
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return decoded
    except JWTError as e:
        print(f"⚠️ JWT Decode Error: {e}")
        return None
