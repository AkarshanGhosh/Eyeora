# db/connection.py
from __future__ import annotations
from typing import AsyncGenerator, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from core.settings import settings

_client: Optional[AsyncIOMotorClient] = None

async def get_client() -> AsyncIOMotorClient:
    """
    Singleton Motor client. Lazily created on first use.
    """
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
        # sanity check (won't block long thanks to serverSelectionTimeoutMS)
        await _client.admin.command("ping")
        print("✅ Motor client ready (async)")
    return _client

async def get_db() -> AsyncIOMotorDatabase:
    """
    Simple accessor for the configured database.
    """
    client = await get_client()
    return client[settings.MONGO_DB]

async def lifespan_connect() -> None:
    """
    Optional explicit connect during FastAPI startup.
    """
    await get_client()

async def lifespan_close() -> None:
    """
    Optional explicit close during FastAPI shutdown.
    """
    global _client
    if _client is not None:
        _client.close()
        _client = None
        print("🛑 Motor client closed")
