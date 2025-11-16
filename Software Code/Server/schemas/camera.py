# schemas/camera.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime

# --- Inputs ---
class CameraCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    uid: str = Field(min_length=1, max_length=50, description="Unique camera identifier")
    image_url: Optional[HttpUrl] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = Field(default=True)

class CameraUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    image_url: Optional[HttpUrl] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

# --- Outputs ---
class CameraPublic(BaseModel):
    id: str
    name: str
    uid: str
    image_url: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str  # admin email who created it