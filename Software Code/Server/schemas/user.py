# schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# --- Inputs ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    role: str = Field(default="user", description="user | admin")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Outputs ---
class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "user"

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
