# api/repositories/user_repo.py
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Optional

from security.hash.get_password_hash import get_password_hash

async def create_user(db: AsyncIOMotorDatabase, email: str, password: str, full_name: str = "", role: str = "user"):
    """Create a new user document with hashed password"""
    existing = await db["users"].find_one({"email": email})
    if existing:
        raise ValueError("User already exists")

    user_doc = {
        "email": email,
        "password": get_password_hash(password),
        "full_name": full_name,
        "role": role
    }

    result = await db["users"].insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    del user_doc["password"]
    return user_doc

async def find_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[dict]:
    """Find user by email"""
    user = await db["users"].find_one({"email": email})
    if not user:
        return None
    user["_id"] = str(user["_id"])
    return user
