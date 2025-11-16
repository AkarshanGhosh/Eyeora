# schemas/analytics.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserStats(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    regular_users: int
    recent_signups: int  # last 7 days

class CameraStats(BaseModel):
    total_cameras: int
    active_cameras: int
    inactive_cameras: int
    cameras_by_location: dict

class MediaStats(BaseModel):
    total_videos: int
    total_images: int
    processed_videos: List[dict]
    processed_images: List[dict]
    storage_used_mb: float

class SystemStats(BaseModel):
    online_users: int  # currently authenticated users
    active_live_streams: int
    processing_jobs: int

class DashboardAnalytics(BaseModel):
    user_stats: UserStats
    camera_stats: CameraStats
    media_stats: MediaStats
    system_stats: SystemStats
    last_updated: datetime