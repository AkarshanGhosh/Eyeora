# security/deps/get_current_user.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from security.jwt.decode_access_token import decode_access_token
from db.connection import get_db
from api.repositories import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
) -> dict:
    """
    Validate token and return current user data from database.
    Returns: {"id": str, "email": str, "full_name": str, "role": str}
    Password is never included in the response.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = decode_access_token(token)
        
        if payload is None:
            raise credentials_exception
        
        # Extract user ID from token
        user_id = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
        # Fetch complete user data from database (excluding password)
        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)
        
        if user is None:
            # If user_id is actually an email (legacy), try fetching by email
            user = await repo.get_by_email(user_id)
        
        if user is None:
            raise credentials_exception
        
        # Return user data WITHOUT password
        return {
            "id": str(user["_id"]),
            "email": user["email"],
            "full_name": user.get("full_name"),
            "role": user.get("role", "user")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_current_user: {e}")
        raise credentials_exception

__all__ = ["get_current_user"]