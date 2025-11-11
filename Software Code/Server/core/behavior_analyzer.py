"""
Shopping Behavior Analysis Module
Determines customer behavior: window shopping, browsing, purchasing
Location: Software Code/Server/core/behavior_analyzer.py
"""

import numpy as np
from typing import List, Dict, Tuple
from enum import Enum

from core.tracker import Track
from core.config import (
    ENTRY_ZONE, EXIT_ZONE, CHECKOUT_ZONE,
    IDLE_TIME_THRESHOLD, BROWSING_TIME_THRESHOLD,
    BEHAVIOR_TYPES
)


class BehaviorType(Enum):
    """Types of shopping behavior"""
    WINDOW_SHOPPING = "window_shopping"  # Quick look, minimal browsing
    BROWSING = "browsing"  # Looking around, spending time
    PURCHASING = "purchasing"  # Went to checkout area
    IDLE = "idle"  # Standing still for long time
    PASSING_THROUGH = "passing_through"  # Just walking through


class ZoneDetector:
    """Detects which zones a person visits"""
    
    def __init__(self, frame_width: int, frame_height: int):
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Calculate actual pixel zones
        self.entry_zone = self._calculate_zone_pixels(ENTRY_ZONE)
        self.exit_zone = self._calculate_zone_pixels(EXIT_ZONE)
        self.checkout_zone = self._calculate_zone_pixels(CHECKOUT_ZONE)
    
    def _calculate_zone_pixels(self, zone_config: Dict) -> Dict:
        """Convert zone ratios to pixel coordinates"""
        return {
            "x_min": int(zone_config["x_start"] * self.frame_width),
            "x_max": int(zone_config["x_end"] * self.frame_width),
            "y_min": int(zone_config["y_start"] * self.frame_height),
            "y_max": int(zone_config["y_end"] * self.frame_height)
        }
    
    def point_in_zone(self, point: Tuple[float, float], zone: Dict) -> bool:
        """Check if point is inside zone"""
        x, y = point
        return (zone["x_min"] <= x <= zone["x_max"] and 
                zone["y_min"] <= y <= zone["y_max"])
    
    def get_zone_name(self, point: Tuple[float, float]) -> str:
        """Get zone name for a point"""
        if self.point_in_zone(point, self.entry_zone):
            return "entry"
        elif self.point_in_zone(point, self.exit_zone):
            return "exit"
        elif self.point_in_zone(point, self.checkout_zone):
            return "checkout"
        else:
            return "main_area"


class BehaviorAnalyzer:
    """
    Analyzes customer behavior based on their tracked movement
    """
    
    def __init__(self, frame_width: int, frame_height: int, fps: float = 30.0):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps
        self.zone_detector = ZoneDetector(frame_width, frame_height)
    
    def analyze_track(self, track: Track) -> Dict:
        """
        Analyze a complete track to determine behavior
        
        Returns:
            Dictionary with behavior analysis results
        """
        if len(track.positions) < 5:  # Not enough data
            return {
                "behavior": BehaviorType.PASSING_THROUGH.value,
                "confidence": 0.5,
                "details": "Insufficient tracking data"
            }
        
        # Analyze zones visited
        zones_visited = self._analyze_zones(track)
        
        # Check if person visited checkout
        visited_checkout = "checkout" in zones_visited
        
        # Calculate metrics
        duration = track.duration
        movement_distance = track.movement_distance
        is_stationary = self._check_if_stationary(track)
        
        # Determine behavior
        behavior = self._determine_behavior(
            duration=duration,
            movement_distance=movement_distance,
            zones_visited=zones_visited,
            visited_checkout=visited_checkout,
            is_stationary=is_stationary,
            track=track
        )
        
        return {
            "track_id": track.track_id,
            "uuid": track.uuid,
            "behavior": behavior["type"],
            "confidence": behavior["confidence"],
            "duration": duration,
            "zones_visited": zones_visited,
            "visited_checkout": visited_checkout,
            "made_purchase": visited_checkout,  # Simplified assumption
            "movement_distance": movement_distance,
            "is_stationary": is_stationary,
            "entry_time": track.entry_time,
            "exit_time": track.exit_time,
            "details": behavior["details"]
        }
    
    def _analyze_zones(self, track: Track) -> List[str]:
        """Analyze which zones person visited"""
        zones = set()
        
        for position in track.positions:
            zone_name = self.zone_detector.get_zone_name(position)
            zones.add(zone_name)
        
        return list(zones)
    
    def _check_if_stationary(self, track: Track) -> bool:
        """Check if person spent significant time stationary"""
        if len(track.positions) < 10:
            return False
        
        # Check last 30 frames (1 second at 30fps)
        check_frames = min(30, len(track.positions))
        recent_positions = track.positions[-check_frames:]
        
        x_coords = [p[0] for p in recent_positions]
        y_coords = [p[1] for p in recent_positions]
        
        x_std = np.std(x_coords)
        y_std = np.std(y_coords)
        
        # If standard deviation is low, person is stationary
        return x_std < 20 and y_std < 20
    
    def _determine_behavior(
        self, 
        duration: float,
        movement_distance: float,
        zones_visited: List[str],
        visited_checkout: bool,
        is_stationary: bool,
        track: Track
    ) -> Dict:
        """
        Determine behavior type based on metrics
        
        Returns:
            Dictionary with behavior type, confidence, and details
        """
        
        # PURCHASING: Visited checkout zone
        if visited_checkout:
            return {
                "type": BehaviorType.PURCHASING.value,
                "confidence": 0.9,
                "details": "Customer visited checkout area"
            }
        
        # IDLE: Standing still for long time
        if is_stationary and duration > IDLE_TIME_THRESHOLD:
            return {
                "type": BehaviorType.IDLE.value,
                "confidence": 0.85,
                "details": f"Person stationary for {duration:.1f}s"
            }
        
        # PASSING_THROUGH: Quick transit
        if duration < 3.0 and movement_distance < 100:
            return {
                "type": BehaviorType.PASSING_THROUGH.value,
                "confidence": 0.8,
                "details": "Quick transit through store"
            }
        
        # BROWSING vs WINDOW_SHOPPING based on time spent
        if duration >= BROWSING_TIME_THRESHOLD:
            # Check movement pattern
            avg_movement = movement_distance / duration if duration > 0 else 0
            
            if avg_movement > 10:  # Active browsing
                return {
                    "type": BehaviorType.BROWSING.value,
                    "confidence": 0.85,
                    "details": f"Active browsing for {duration:.1f}s, moved {movement_distance:.0f}px"
                }
            else:  # Less movement but spending time
                return {
                    "type": BehaviorType.BROWSING.value,
                    "confidence": 0.75,
                    "details": f"Browsing with limited movement for {duration:.1f}s"
                }
        else:
            # Window shopping - quick look
            return {
                "type": BehaviorType.WINDOW_SHOPPING.value,
                "confidence": 0.8,
                "details": f"Brief visit of {duration:.1f}s, possibly window shopping"
            }
    
    def generate_summary(self, analyzed_tracks: List[Dict]) -> Dict:
        """
        Generate summary statistics from analyzed tracks
        
        Returns:
            Summary dictionary with counts and metrics
        """
        if not analyzed_tracks:
            return {
                "total_visitors": 0,
                "total_customers": 0,
                "window_shoppers": 0,
                "browsers": 0,
                "purchasers": 0,
                "conversion_rate": 0.0,
                "avg_visit_duration": 0.0
            }
        
        total_visitors = len(analyzed_tracks)
        purchasers = sum(1 for t in analyzed_tracks 
                        if t["behavior"] == BehaviorType.PURCHASING.value)
        browsers = sum(1 for t in analyzed_tracks 
                      if t["behavior"] == BehaviorType.BROWSING.value)
        window_shoppers = sum(1 for t in analyzed_tracks 
                             if t["behavior"] == BehaviorType.WINDOW_SHOPPING.value)
        
        avg_duration = np.mean([t["duration"] for t in analyzed_tracks])
        conversion_rate = (purchasers / total_visitors * 100) if total_visitors > 0 else 0
        
        return {
            "total_visitors": total_visitors,
            "total_customers": purchasers,
            "window_shoppers": window_shoppers,
            "browsers": browsers,
            "purchasers": purchasers,
            "passing_through": sum(1 for t in analyzed_tracks 
                                   if t["behavior"] == BehaviorType.PASSING_THROUGH.value),
            "idle": sum(1 for t in analyzed_tracks 
                       if t["behavior"] == BehaviorType.IDLE.value),
            "conversion_rate": round(conversion_rate, 2),
            "avg_visit_duration": round(avg_duration, 2),
            "total_checkout_visitors": sum(1 for t in analyzed_tracks 
                                          if t["visited_checkout"])
        }


def draw_zones(frame: np.ndarray, zone_detector: ZoneDetector) -> np.ndarray:
    """
    Draw zone boundaries on frame for visualization
    
    Args:
        frame: Video frame
        zone_detector: ZoneDetector instance
        
    Returns:
        Frame with zones drawn
    """
    import cv2
    
    # Draw entry zone (green)
    z = zone_detector.entry_zone
    cv2.rectangle(frame, (z["x_min"], z["y_min"]), (z["x_max"], z["y_max"]), 
                 (0, 255, 0), 2)
    cv2.putText(frame, "ENTRY", (z["x_min"] + 5, z["y_min"] + 25),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Draw exit zone (red)
    z = zone_detector.exit_zone
    cv2.rectangle(frame, (z["x_min"], z["y_min"]), (z["x_max"], z["y_max"]), 
                 (0, 0, 255), 2)
    cv2.putText(frame, "EXIT", (z["x_min"] + 5, z["y_min"] + 25),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Draw checkout zone (blue)
    z = zone_detector.checkout_zone
    cv2.rectangle(frame, (z["x_min"], z["y_min"]), (z["x_max"], z["y_max"]), 
                 (255, 0, 0), 2)
    cv2.putText(frame, "CHECKOUT", (z["x_min"] + 5, z["y_min"] + 25),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    return frame


if __name__ == "__main__":
    print("✅ Behavior Analyzer Module Ready")
    print("📊 Behaviors: Window Shopping, Browsing, Purchasing, Idle, Passing Through")
    print("🎯 Zone Detection: Entry, Exit, Checkout, Main Area")