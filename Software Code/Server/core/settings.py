# core/settings.py
from __future__ import annotations
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Resolve project root:  .../Server/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

class Settings(BaseSettings):
    # Defaults (used only if .env not found / not set)
    MONGO_URI: str = "mongodb+srv://ronighosh494:roniempire@userdetail.flx0d.mongodb.net/"
    MONGO_DB: str = "eyeora_db"

    JWT_SECRET: str = "CHANGE_ME_SUPER_SECRET"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # Tell pydantic-settings where the .env is (absolute path)
    model_config = SettingsConfigDict(env_file=str(ENV_PATH), env_file_encoding="utf-8")

settings = Settings()

# Debug prints about env discovery
print(f"🔎 .env path resolved to: {ENV_PATH}")
print(f"📄 .env exists: {ENV_PATH.exists()}")

# Try connecting to MongoDB once at startup
try:
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    print("✅ MongoDB connection successful!")
    print(f"📦 URI: {settings.MONGO_URI}")
    print(f"🗂️  DB : {settings.MONGO_DB}")
except ConnectionFailure as e:
    print("❌ MongoDB connection failed!")
    print(f"   ↳ {e}")
    print("🛠️  Check: MONGO_URI/MONGO_DB in your .env and Network Access in Atlas.")
except Exception as e:
    print("⚠️ Unexpected error during MongoDB connection check.")
    print(f"   ↳ {e}")
