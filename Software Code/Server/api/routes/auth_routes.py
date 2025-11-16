# api/routes/auth_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any
from db.connection import get_db
from api.repositories import UserRepository
from schemas.user import UserCreate, UserLogin, UserPublic, Token
from security.hash.verify_password import verify_password
from security.hash.get_password_hash import get_password_hash
from security.jwt.create_access_token import create_access_token
from security.deps.get_current_user import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
print("🔌 Auth routes loaded")

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db=Depends(get_db)) -> Any:
    repo = UserRepository(db)
    existing = await repo.get_by_email(user_in.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    hashed = get_password_hash(user_in.password)
    created = await repo.create_user(
        email=user_in.email,
        hashed_password=hashed,
        full_name=user_in.full_name,
        role=user_in.role,
    )
    return UserPublic(
        id=str(created["_id"]), 
        email=created["email"], 
        full_name=created.get("full_name"), 
        role=created.get("role", "user")
    )

@router.post("/login_json", response_model=Token)
async def login_json(payload: UserLogin, db=Depends(get_db)) -> Any:
    repo = UserRepository(db)
    user = await repo.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    await repo.set_last_login(payload.email)
    
    # FIXED: Use consistent payload structure - just the user_id as string in 'sub'
    user_id = str(user["_id"])
    token_data = {
        "sub": user_id,  # Standard JWT claim - subject (user ID)
        "email": user["email"],
        "role": user.get("role", "user")
    }
    token = create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login_form(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)) -> Any:
    repo = UserRepository(db)
    user = await repo.get_by_email(form.username)
    if not user or not verify_password(form.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    await repo.set_last_login(form.username)
    
    # FIXED: Use consistent payload structure
    user_id = str(user["_id"])
    token_data = {
        "sub": user_id,
        "email": user["email"],
        "role": user.get("role", "user")
    }
    token = create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserPublic)
async def me(current_user: dict = Depends(get_current_user)) -> Any:
    """Get current user information"""
    # current_user is already populated by get_current_user dependency
    return UserPublic(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        role=current_user.get("role", "user")
    )

@router.post("/logout")
async def logout(current_user=Depends(get_current_user), db=Depends(get_db)):
    """Logout current user"""
    try:
        from api.repositories import AnalyticsRepository
        analytics_repo = AnalyticsRepository(db)
        await analytics_repo.remove_user_session(current_user["id"])
    except:
        pass  # Session tracking is optional
    return {"message": "Logged out successfully"}