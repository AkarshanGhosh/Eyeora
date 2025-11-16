# api/repositories/analytics_repo.py
from typing import List
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
from pathlib import Path
from core.config import PROCESSED_DIR

class AnalyticsRepository:
    """
    Repository for admin analytics and statistics.
    """
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_col = db["users"]
        self.cameras_col = db["cameras"]
        self.sessions_col = db["active_sessions"]  # for tracking online users

    async def get_user_stats(self) -> dict:
        """Get user statistics"""
        total = await self.users_col.count_documents({})
        active = await self.users_col.count_documents({"is_active": True})
        admins = await self.users_col.count_documents({"role": "admin"})
        regular = total - admins
        
        # Recent signups (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent = await self.users_col.count_documents({
            "created_at": {"$gte": seven_days_ago}
        })
        
        return {
            "total_users": total,
            "active_users": active,
            "admin_users": admins,
            "regular_users": regular,
            "recent_signups": recent
        }

    async def get_camera_stats(self) -> dict:
        """Get camera statistics"""
        total = await self.cameras_col.count_documents({})
        active = await self.cameras_col.count_documents({"is_active": True})
        inactive = total - active
        
        # Cameras by location
        pipeline = [
            {"$group": {"_id": "$location", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        locations = await self.cameras_col.aggregate(pipeline).to_list(length=None)
        cameras_by_location = {
            item["_id"] if item["_id"] else "Unknown": item["count"] 
            for item in locations
        }
        
        return {
            "total_cameras": total,
            "active_cameras": active,
            "inactive_cameras": inactive,
            "cameras_by_location": cameras_by_location
        }

    async def get_media_stats(self) -> dict:
        """Get media file statistics"""
        processed_videos_dir = PROCESSED_DIR / "videos"
        processed_images_dir = PROCESSED_DIR / "images"
        
        videos = []
        images = []
        total_size = 0
        
        # Get processed videos
        if processed_videos_dir.exists():
            for file in processed_videos_dir.iterdir():
                if file.is_file() and file.suffix in ['.mp4', '.avi', '.mov']:
                    stat = file.stat()
                    videos.append({
                        "filename": file.name,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "url": f"/processed/videos/{file.name}"
                    })
                    total_size += stat.st_size
        
        # Get processed images
        if processed_images_dir.exists():
            for file in processed_images_dir.iterdir():
                if file.is_file() and file.suffix in ['.jpg', '.jpeg', '.png']:
                    stat = file.stat()
                    images.append({
                        "filename": file.name,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "url": f"/processed/images/{file.name}"
                    })
                    total_size += stat.st_size
        
        return {
            "total_videos": len(videos),
            "total_images": len(images),
            "processed_videos": sorted(videos, key=lambda x: x["created_at"], reverse=True),
            "processed_images": sorted(images, key=lambda x: x["created_at"], reverse=True),
            "storage_used_mb": round(total_size / (1024 * 1024), 2)
        }

    async def get_online_users_count(self) -> int:
        """Get count of currently online users"""
        # Sessions older than 30 minutes are considered expired
        thirty_mins_ago = datetime.utcnow() - timedelta(minutes=30)
        return await self.sessions_col.count_documents({
            "last_activity": {"$gte": thirty_mins_ago}
        })

    async def track_user_session(self, user_id: str):
        """Track user activity for online status"""
        await self.sessions_col.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "last_activity": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

    async def remove_user_session(self, user_id: str):
        """Remove user session on logout"""
        await self.sessions_col.delete_one({"user_id": user_id})

__all__ = ["AnalyticsRepository"]