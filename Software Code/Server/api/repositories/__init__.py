# api/repositories/__init__.py
from .user_repo import UserRepository
from .camera_repo import CameraRepository
from .analytics_repo import AnalyticsRepository

__all__ = ["UserRepository", "CameraRepository", "AnalyticsRepository"]