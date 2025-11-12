# api/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase

from db.connection import get_db
from api.repositories.user_repo import create_user, find_by_email
from security.hash.verify_password import verify_password
from security.jwt.create_access_token import create_access_token
from security.deps.get_current_user import get_current_user
from schemas.user import UserCreate, UserLogin, UserPublic, Token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        user = await create_user(
            db=db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name or "",
            role=payload.role or "user",
        )
        # normalize output to UserPublic
        return {
            "id": user["_id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "role": user.get("role", "user"),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

# OAuth2-compliant login (form data: username, password)
@router.post("/login", response_model=Token)
async def login_oauth2(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    # OAuth2 form uses "username" field for email
    email = form.username.lower()
    user = await find_by_email(db, email)
    if not user or not verify_password(form.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(sub=user["_id"], role=user.get("role", "user"))
    return {"access_token": token, "token_type": "bearer"}

# JSON-body login (convenient for frontend)
@router.post("/login_json", response_model=Token)
async def login_json(payload: UserLogin, db: AsyncIOMotorDatabase = Depends(get_db)):
    email = payload.email.lower()
    user = await find_by_email(db, email)
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(sub=user["_id"], role=user.get("role", "user"))
    return {"access_token": token, "token_type": "bearer"}

# Who am I (requires valid Bearer token)
@router.get("/me", response_model=UserPublic)
async def me(current=Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    # current = {"id": "...", "role": "..."}
    user = await find_by_email(db, email=None)  # optional: fetch full doc by _id if you prefer
    # Since we only have id/role from token, return minimal info for now
    return {
        "id": current["id"],
        "email": "hidden@domain",  # optional: lookup by _id to return real email
        "full_name": None,
        "role": current.get("role", "user"),
    }
