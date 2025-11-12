from fastapi import Depends, HTTPException, status
from security.deps.oauth2 import oauth2_scheme
from security.jwt.decode_token import decode_token

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    data = decode_token(token)
    if not data or "sub" not in data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return {"id": data["sub"], "role": data.get("role", "user")}
