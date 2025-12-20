"""
Core Package - Eyeora AI-CCTV
Location: Software Code/Server/core/__init__.py
"""

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
from .config import *

# -------------------------------------------------------------------
# Tracking & Data Structures
# -------------------------------------------------------------------
from .tracker import Track, Detection, PersonTracker

# -------------------------------------------------------------------
# Behavior Analysis
# -------------------------------------------------------------------
from .behavior_analyzer import BehaviorAnalyzer, BehaviorType, ZoneDetector

# -------------------------------------------------------------------
# Detection Engine (Enhanced)
# -------------------------------------------------------------------
from .detection_engine import (
    EnhancedDetectionEngine,
    AbnormalityDetector
)

# Backward compatibility alias:
DetectionEngine = EnhancedDetectionEngine

class ModelManager:
    """
    Backward-compatible placeholder.
    Models are now handled internally by DetectionEngine.
    """
    pass

# -------------------------------------------------------------------
# Export & Alerts
# -------------------------------------------------------------------
from .csv_exporter import DataExporter
from .alert_system import AlertSystem, Alert, AlertType, AlertLevel

# -------------------------------------------------------------------
# IMPORTANT:
# Do NOT import VideoProcessor here to avoid circular imports.
# Access it via: from core.video_processor import VideoProcessor
# -------------------------------------------------------------------

__all__ = [
    # Tracking
    'Track',
    'Detection',
    'PersonTracker',

    # Behavior
    'BehaviorAnalyzer',
    'BehaviorType',
    'ZoneDetector',

    # Detection
    'DetectionEngine',
    'EnhancedDetectionEngine',
    'AbnormalityDetector',
    'ModelManager',

    # Export
    'DataExporter',

    # Alerts
    'AlertSystem',
    'Alert',
    'AlertType',
    'AlertLevel',

    # NOTE: VideoProcessor intentionally NOT exported here
]
