# security/deps/require_admin.py
from fastapi import Depends, HTTPException, status
from security.deps.get_current_user import get_current_user

async def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Dependency that ensures current user has admin role.
    Raises 403 if user is not admin.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

__all__ = ["require_admin"]