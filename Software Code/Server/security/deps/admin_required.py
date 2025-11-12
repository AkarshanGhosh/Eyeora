from fastapi import Depends, HTTPException, status
from security.deps.get_current_user import get_current_user

async def admin_required(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user
