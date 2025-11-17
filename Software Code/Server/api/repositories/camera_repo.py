# api/repositories/camera_repo.py
from typing import Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from urllib.parse import unquote

class CameraRepository:
    """
    CRUD operations for cameras collection.
    """
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["cameras"]

    async def get_by_uid(self, uid: str) -> Optional[dict]:
        # Decode URL-encoded UID
        decoded_uid = unquote(uid)
        return await self.col.find_one({"uid": decoded_uid})

    async def get_by_id(self, camera_id: str) -> Optional[dict]:
        decoded_id = unquote(camera_id)
        return await self.col.find_one({"_id": decoded_id})

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[dict]:
        cursor = self.col.find().skip(skip).limit(limit).sort("created_at", -1)
        return await cursor.to_list(length=limit)

    async def create_camera(
        self,
        *,
        uid: str,
        name: str,
        image_url: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        is_active: bool = True,
        created_by: str,
    ) -> dict:
        doc = {
            "_id": uid,  # using uid as primary key
            "uid": uid,
            "name": name,
            "image_url": image_url,
            "location": location,
            "description": description,
            "is_active": is_active,
            "created_by": created_by,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        await self.col.insert_one(doc)
        return doc

    async def update_camera(self, uid: str, update_data: dict) -> bool:
        decoded_uid = unquote(uid)
        update_data["updated_at"] = datetime.utcnow()
        result = await self.col.update_one(
            {"uid": decoded_uid},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete_camera(self, uid: str) -> bool:
        decoded_uid = unquote(uid)
        result = await self.col.delete_one({"uid": decoded_uid})
        return result.deleted_count > 0

__all__ = ["CameraRepository"]