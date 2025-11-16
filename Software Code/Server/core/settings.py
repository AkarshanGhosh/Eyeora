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
    # MongoDB Configuration
    MONGO_URI: str = "mongodb+srv://ronighosh494:roniempire@userdetail.flx0d.mongodb.net/"
    MONGO_DB: str = "eyeora_db"

    # JWT/Security Configuration
    SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET"
    JWT_SECRET: str = "CHANGE_ME_SUPER_SECRET"  # Alias for backwards compatibility
    JWT_ALG: str = "HS256"
    ALGORITHM: str = "HS256"  # Alias for consistency
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # Application Configuration
    APP_NAME: str = "Eyeora"
    DEBUG: bool = False
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS Configuration
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    # File Paths
    @property
    def models_dir(self) -> Path:
        return PROJECT_ROOT / "core" / "models"
    
    @property
    def data_dir(self) -> Path:
        return PROJECT_ROOT / "core" / "data"
    
    @property
    def reports_dir(self) -> Path:
        return PROJECT_ROOT / "core" / "data" / "reports"

    # Camera & Detection Settings
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.5
    MAX_DETECTION_AGE: int = 300
    DEFAULT_CAMERA_FPS: int = 30
    MAX_CAMERAS: int = 50

    # Analytics
    ANALYTICS_RETENTION_DAYS: int = 90

    # Tell pydantic-settings where the .env is (absolute path)
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH), 
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"  # Allow extra fields
    )

    @property
    def secret_key(self) -> str:
        """Unified accessor for secret key"""
        return self.SECRET_KEY or self.JWT_SECRET

    @property
    def algorithm(self) -> str:
        """Unified accessor for algorithm"""
        return self.ALGORITHM or self.JWT_ALG

# Create global settings instance
settings = Settings()

# Ensure directories exist
settings.models_dir.mkdir(parents=True, exist_ok=True)
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.reports_dir.mkdir(parents=True, exist_ok=True)

# Debug prints about env discovery
print(f"🔎 .env path resolved to: {ENV_PATH}")
print(f"📄 .env exists: {ENV_PATH.exists()}")
print(f"🔑 SECRET_KEY loaded: {'Yes' if settings.SECRET_KEY != 'CHANGE_ME_SUPER_SECRET' else 'No (using default)'}")

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

print(f"✅ Configuration loaded successfully")
print(f"📁 Models directory: {settings.models_dir}")
print(f"📁 Data directory: {settings.data_dir}")
print(f"📁 Reports directory: {settings.reports_dir}")