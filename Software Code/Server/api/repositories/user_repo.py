# api/repositories/user_repo.py
from typing import Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

class UserRepository:
    """
    Thin CRUD wrapper around the `users` collection.
    Stores hashed passwords. Never store plaintext.
    Password field is excluded from return values where appropriate.
    """
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["users"]

    async def get_by_email(self, email: str, include_password: bool = True) -> Optional[dict]:
        """
        Get user by email.
        
        Args:
            email: User's email address
            include_password: If False, excludes password from result (default: True for auth)
        
        Returns:
            User document or None
        """
        if include_password:
            return await self.col.find_one({"email": email.lower()})
        else:
            return await self.col.find_one(
                {"email": email.lower()},
                {"password": 0}  # Exclude password field
            )

    async def get_by_id(self, user_id: str, include_password: bool = False) -> Optional[dict]:
        """
        Get user by ID.
        
        Args:
            user_id: User's ID (email in this schema)
            include_password: If True, includes password (default: False for security)
        
        Returns:
            User document or None
        """
        if include_password:
            return await self.col.find_one({"_id": user_id})
        else:
            return await self.col.find_one(
                {"_id": user_id},
                {"password": 0}  # Exclude password field
            )

    async def create_user(
        self,
        *,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        role: str = "user",
    ) -> dict:
        """
        Create a new user.
        
        Args:
            email: User's email (used as ID)
            hashed_password: Already hashed password
            full_name: Optional full name
            role: User role (default: "user")
        
        Returns:
            Created user document (without password)
        """
        doc = {
            "_id": email.lower(),
            "email": email.lower(),
            "password": hashed_password,
            "full_name": full_name,
            "role": role,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
            "is_active": True,
        }
        await self.col.insert_one(doc)
        
        # Return document without password for security
        doc_without_password = {k: v for k, v in doc.items() if k != "password"}
        return doc_without_password

    async def set_last_login(self, email: str) -> None:
        """Update user's last login timestamp"""
        await self.col.update_one(
            {"email": email.lower()},
            {"$set": {"last_login": datetime.utcnow()}}
        )

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """
        Get all users with pagination.
        Password field is excluded from results.
        
        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
        
        Returns:
            List of user documents without passwords
        """
        cursor = self.col.find(
            {},
            {"password": 0}  # Exclude password from all results
        ).skip(skip).limit(limit).sort("created_at", -1)
        
        return await cursor.to_list(length=limit)

    async def update_user(self, user_id: str, update_data: dict) -> bool:
        """
        Update user fields.
        
        Args:
            user_id: User's ID
            update_data: Dictionary of fields to update
        
        Returns:
            True if user was updated, False otherwise
        """
        # Prevent password from being updated through this method
        if "password" in update_data:
            del update_data["password"]
        
        update_data["updated_at"] = datetime.utcnow()
        result = await self.col.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def update_password(self, user_id: str, hashed_password: str) -> bool:
        """
        Update user password (separate method for security).
        
        Args:
            user_id: User's ID
            hashed_password: New hashed password
        
        Returns:
            True if password was updated, False otherwise
        """
        result = await self.col.update_one(
            {"_id": user_id},
            {"$set": {
                "password": hashed_password,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user by ID.
        
        Args:
            user_id: User's ID
        
        Returns:
            True if user was deleted, False otherwise
        """
        result = await self.col.delete_one({"_id": user_id})
        return result.deleted_count > 0

    async def count_users(self, filter_dict: Optional[dict] = None) -> int:
        """
        Get total user count.
        
        Args:
            filter_dict: Optional filter criteria
        
        Returns:
            Number of users matching filter
        """
        if filter_dict is None:
            filter_dict = {}
        return await self.col.count_documents(filter_dict)

    async def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate user (soft delete).
        
        Args:
            user_id: User's ID
        
        Returns:
            True if user was deactivated, False otherwise
        """
        result = await self.col.update_one(
            {"_id": user_id},
            {"$set": {
                "is_active": False,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    async def activate_user(self, user_id: str) -> bool:
        """
        Activate user.
        
        Args:
            user_id: User's ID
        
        Returns:
            True if user was activated, False otherwise
        """
        result = await self.col.update_one(
            {"_id": user_id},
            {"$set": {
                "is_active": True,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

__all__ = ["UserRepository"]