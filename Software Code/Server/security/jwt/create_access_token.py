# security/jwt/create_access_token.py

from datetime import datetime, timedelta
from jose import jwt
import os

# Get SECRET_KEY from environment - MUST be the same as in get_current_user
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Dictionary containing token claims (sub, email, role, etc.)
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add standard JWT claims
    to_encode.update({"exp": expire})
    
    # Encode the token using the SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt