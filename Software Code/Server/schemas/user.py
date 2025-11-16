# schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# --- Inputs ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    role: str = Field(default="user", description="user | admin")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = Field(None, description="user | admin")
    is_active: Optional[bool] = None

# --- Outputs ---
class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "user"

class UserDetailPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"