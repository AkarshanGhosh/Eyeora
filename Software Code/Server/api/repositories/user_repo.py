# api/repositories/user_repo.py
from typing import Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

class UserRepository:
    """
    Thin CRUD wrapper around the `users` collection.
    Stores hashed passwords. Never store plaintext.
    """
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["users"]

    async def get_by_email(self, email: str) -> Optional[dict]:
        return await self.col.find_one({"email": email})

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        return await self.col.find_one({"_id": user_id})

    async def create_user(
        self,
        *,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        role: str = "user",
    ) -> dict:
        doc = {
            "_id": email.lower(),              # use email as id for simplicity
            "email": email.lower(),
            "password": hashed_password,
            "full_name": full_name,
            "role": role,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
        }
        await self.col.insert_one(doc)
        return doc

    async def set_last_login(self, email: str) -> None:
        await self.col.update_one(
            {"email": email.lower()},
            {"$set": {"last_login": datetime.utcnow()}}
        )

__all__ = ["UserRepository"]
