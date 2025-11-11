"""
Configuration file for the Eyeora AI-CCTV Platform
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
UPLOADS_DIR = BASE_DIR / "Uploads"
PROCESSED_DIR = BASE_DIR / "processed"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"

# Create necessary directories
for directory in [MODELS_DIR, UPLOADS_DIR, PROCESSED_DIR, STATIC_DIR, DATA_DIR, REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
    
# Sub-directories
(UPLOADS_DIR / "images").mkdir(exist_ok=True)
(UPLOADS_DIR / "videos").mkdir(exist_ok=True)
(PROCESSED_DIR / "images").mkdir(exist_ok=True)
(PROCESSED_DIR / "videos").mkdir(exist_ok=True)
(DATA_DIR / "csv").mkdir(exist_ok=True)

# Model Configuration
YOLO_MODEL = "yolo11x.pt"  # Best accuracy for retail analytics
MODEL_PATH = MODELS_DIR / YOLO_MODEL

# Detection Parameters
CONFIDENCE_THRESHOLD = 0.4  # Confidence threshold for detections
IOU_THRESHOLD = 0.45  # IoU threshold for NMS
MAX_DETECTIONS = 100  # Maximum detections per frame

# Tracking Configuration
TRACK_MAX_AGE = 30  # Maximum frames to keep track without detection
TRACK_MIN_HITS = 3  # Minimum hits to confirm a track
TRACK_IOU_THRESHOLD = 0.3  # IoU threshold for matching detections to tracks

# Behavior Analysis Configuration
IDLE_TIME_THRESHOLD = 5.0  # Seconds - person standing still
BROWSING_TIME_THRESHOLD = 3.0  # Seconds - minimum time to consider as browsing
EXIT_ZONE_RATIO = 0.3  # Ratio of frame width for exit zone detection
ENTRY_ZONE_RATIO = 0.3  # Ratio of frame width for entry zone detection

# Zone Definitions (percentage of frame)
ENTRY_ZONE = {
    "x_start": 0.0,
    "x_end": 0.3,
    "y_start": 0.0,
    "y_end": 1.0
}

EXIT_ZONE = {
    "x_start": 0.7,
    "x_end": 1.0,
    "y_start": 0.0,
    "y_end": 1.0
}

CHECKOUT_ZONE = {
    "x_start": 0.4,
    "x_end": 0.6,
    "y_start": 0.7,
    "y_end": 1.0
}

# Video Processing
VIDEO_FPS_PROCESS = 10  # Process every Nth frame for faster processing
VIDEO_OUTPUT_FPS = 15  # Output video FPS

# CSV Export Configuration
CSV_COLUMNS = [
    "timestamp",
    "person_id",
    "entry_time",
    "exit_time",
    "duration_seconds",
    "behavior",
    "visited_zones",
    "made_purchase",
    "confidence"
]

# Behavior Types
BEHAVIOR_TYPES = {
    "WINDOW_SHOPPING": "window_shopping",
    "BROWSING": "browsing",
    "PURCHASING": "purchasing",
    "IDLE": "idle",
    "PASSING_THROUGH": "passing_through"
}

# Alert Configuration
ALERT_TYPES = {
    "SECURITY": ["person", "backpack", "handbag", "suitcase"],
    "SAFETY": ["fire", "smoke"],
    "CROWD": "crowd_detected"
}

CROWD_THRESHOLD = 10  # Number of people to trigger crowd alert

# Server Configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000
RELOAD_SERVER = True

# Database Configuration (MongoDB)
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "eyeora_db"
COLLECTION_PEOPLE = "people_tracking"
COLLECTION_ANALYTICS = "daily_analytics"
COLLECTION_ALERTS = "alerts"

# Camera Configuration
CAMERA_UID_LENGTH = 12
DEFAULT_CAMERA_INDEX = 0

# File size limits
MAX_VIDEO_SIZE_MB = 500
MAX_IMAGE_SIZE_MB = 10

# Export formats
EXPORT_FORMATS = ["csv", "json", "excel"]

print(f"✅ Configuration loaded successfully")
print(f"📁 Models directory: {MODELS_DIR}")
print(f"📁 Data directory: {DATA_DIR}")
print(f"📁 Reports directory: {REPORTS_DIR}")