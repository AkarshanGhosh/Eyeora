# db/startup/create_indexes.py
from motor.motor_asyncio import AsyncIOMotorDatabase

async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    # users
    await db["users"].create_index("email", unique=True, name="uniq_email")
    await db["users"].create_index("role", name="idx_role")
    # cameras
    await db["cameras"].create_index("owner_id", name="idx_owner")
    await db["cameras"].create_index("name", name="idx_name")
    print("🔧 MongoDB indexes ensured")
