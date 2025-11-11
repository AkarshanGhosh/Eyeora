"""
Core Package - Eyeora AI-CCTV
Location: Software Code/Server/core/__init__.py
"""

# This file makes the core directory a Python package

from .config import *
from .tracker import Track, Detection, PersonTracker
from .behavior_analyzer import BehaviorAnalyzer, BehaviorType, ZoneDetector
from .csv_exporter import DataExporter
from .detection_engine import DetectionEngine, ModelManager
from .alert_system import AlertSystem, Alert, AlertType, AlertLevel
from .video_processor import VideoProcessor

__all__ = [
    'Track',
    'Detection',
    'PersonTracker',
    'BehaviorAnalyzer',
    'BehaviorType',
    'ZoneDetector',
    'DataExporter',
    'DetectionEngine',
    'ModelManager',
    'AlertSystem',
    'Alert',
    'AlertType',
    'AlertLevel',
    'VideoProcessor',
]