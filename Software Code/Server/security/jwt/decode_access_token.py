# security/jwt/decode_access_token.py

from jose import jwt, JWTError
import os
from typing import Optional

# IMPORTANT: Must match the SECRET_KEY used in create_access_token
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify JWT access token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload dict if valid, None if invalid
    """
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print(f"JWT decode error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error decoding token: {e}")
        return None

__all__ = ["decode_access_token"]