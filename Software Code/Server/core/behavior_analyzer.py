"""
Shopping Behavior Analysis Module
Determines customer behavior: window shopping, browsing, purchasing
Location: Software Code/Server/core/behavior_analyzer.py

Behavior Analyzer - FIXED & ENHANCED VERSION
Includes:
- Original zone-based behavior analysis using Track objects
- Safe summary generation (no KeyError: 'duration')
- Additional metrics: stops, stationary time, distance, average speed
- Business insights and recommendations based on behavior distribution
"""

import numpy as np
from typing import List, Dict, Tuple, Any
from enum import Enum
from collections import Counter
from datetime import datetime

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
    Analyzes customer behavior based on their tracked movement (Track object)
    and provides additional metrics & insights for raw track dictionaries.
    """
    
    def __init__(self, frame_width: int, frame_height: int, fps: float = 30.0):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps
        self.zone_detector = ZoneDetector(frame_width, frame_height)

        # New behavior rule set (from new code)
        self.behavior_rules = {
            'purchasing': {'min_duration': 30, 'min_stops': 2},
            'window_shopping': {'min_duration': 15, 'max_duration': 45},
            'browsing': {'min_duration': 10, 'min_stops': 1},
            'passing_through': {'max_duration': 10, 'max_stops': 1},
            'idle': {'min_stationary_time': 20}
        }
    
    # ---------------- ORIGINAL ANALYSIS USING Track ---------------- #

    def analyze_track(self, track: Track) -> Dict:
        """
        Analyze a complete track to determine behavior
        
        Returns:
            Dictionary with behavior analysis results
        """
        if len(track.positions) < 5:  # Not enough data
            return {
                "track_id": track.track_id,
                "uuid": getattr(track, "uuid", None),
                "behavior": BehaviorType.PASSING_THROUGH.value,
                "confidence": 0.5,
                "details": "Insufficient tracking data",
                "duration": track.duration if hasattr(track, "duration") else 0.0,
                "zones_visited": [],
                "visited_checkout": False,
                "made_purchase": False,
                "movement_distance": getattr(track, "movement_distance", 0.0),
                "is_stationary": False,
                "entry_time": getattr(track, "entry_time", None),
                "exit_time": getattr(track, "exit_time", None)
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

    # ---------------- NEW: RAW TRACK ANALYSIS (DICT-BASED) ---------------- #

    def analyze_track_dict(self, track_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single person track provided as a plain dictionary.
        This is the dict-based version from the new code, adapted to coexist.
        
        Args:
            track_data: Dictionary with keys like:
                - 'track_id'
                - 'positions': list of (x, y)
                - 'timestamps': list of timestamps (seconds)
        
        Returns:
            Dictionary with analysis results (duration, distance, stops, behavior, etc.)
        """
        try:
            # Extract basic info with safe defaults
            track_id = track_data.get('track_id', 0)
            positions = track_data.get('positions', [])
            timestamps = track_data.get('timestamps', [])
            
            # Calculate duration safely
            if timestamps and len(timestamps) > 0:
                duration = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0
            else:
                duration = 0
            
            # Calculate movement metrics
            total_distance = self._calculate_total_distance(positions)
            avg_speed = total_distance / duration if duration > 0 else 0
            
            # Detect stops/pauses
            stops = self._detect_stops(positions, timestamps)
            num_stops = len(stops)
            
            # Calculate stationary time
            stationary_time = sum(stop['duration'] for stop in stops)
            
            # Classify behavior (string labels as in new code)
            behavior_label = self._classify_behavior(
                duration=duration,
                num_stops=num_stops,
                stationary_time=stationary_time,
                total_distance=total_distance
            )
            
            # Determine zones visited (simplified)
            zones_visited = self._identify_zones(positions)
            
            # Check if person made a purchase (simplified - based on checkout zone)
            made_purchase = 'checkout' in zones_visited
            
            return {
                'track_id': track_id,
                'duration': float(duration),  # Ensure it's a float
                'total_distance': float(total_distance),
                'avg_speed': float(avg_speed),
                'num_stops': int(num_stops),
                'stationary_time': float(stationary_time),
                'behavior': behavior_label,
                'zones_visited': zones_visited,
                'made_purchase': made_purchase,
                'stops': stops,
                'first_seen': timestamps[0] if timestamps else 0,
                'last_seen': timestamps[-1] if timestamps else 0
            }
            
        except Exception as e:
            print(f"❌ Error analyzing raw track: {e}")
            # Return safe defaults
            return {
                'track_id': track_data.get('track_id', 0),
                'duration': 0.0,
                'total_distance': 0.0,
                'avg_speed': 0.0,
                'num_stops': 0,
                'stationary_time': 0.0,
                'behavior': 'unknown',
                'zones_visited': [],
                'made_purchase': False,
                'stops': [],
                'first_seen': 0,
                'last_seen': 0
            }

    def _calculate_total_distance(self, positions: List) -> float:
        """Calculate total distance traveled (for dict-based analysis)"""
        if len(positions) < 2:
            return 0.0
        
        total = 0.0
        for i in range(1, len(positions)):
            if len(positions[i]) >= 2 and len(positions[i-1]) >= 2:
                dx = positions[i][0] - positions[i-1][0]
                dy = positions[i][1] - positions[i-1][1]
                total += np.sqrt(dx**2 + dy**2)
        
        return float(total)
    
    def _detect_stops(self, positions: List, timestamps: List) -> List[Dict]:
        """Detect stops/pauses in movement (dict-based analysis)"""
        if len(positions) < 2 or len(timestamps) < 2:
            return []
        
        stops = []
        movement_threshold = 10  # pixels
        min_stop_duration = 2.0  # seconds
        
        in_stop = False
        stop_start_idx = 0
        
        for i in range(1, len(positions)):
            if len(positions[i]) >= 2 and len(positions[i-1]) >= 2:
                dx = positions[i][0] - positions[i-1][0]
                dy = positions[i][1] - positions[i-1][1]
                distance = np.sqrt(dx**2 + dy**2)
                
                if distance < movement_threshold:
                    if not in_stop:
                        in_stop = True
                        stop_start_idx = i - 1
                else:
                    if in_stop:
                        duration = timestamps[i-1] - timestamps[stop_start_idx]
                        if duration >= min_stop_duration:
                            stops.append({
                                'start_time': timestamps[stop_start_idx],
                                'end_time': timestamps[i-1],
                                'duration': float(duration),
                                'position': positions[stop_start_idx]
                            })
                        in_stop = False
        
        # Check if still in stop at end
        if in_stop and len(timestamps) > stop_start_idx:
            duration = timestamps[-1] - timestamps[stop_start_idx]
            if duration >= min_stop_duration:
                stops.append({
                    'start_time': timestamps[stop_start_idx],
                    'end_time': timestamps[-1],
                    'duration': float(duration),
                    'position': positions[stop_start_idx]
                })
        
        return stops
    
    def _classify_behavior(self, duration: float, num_stops: int, 
                           stationary_time: float, total_distance: float) -> str:
        """Classify person's behavior based on metrics (dict-based classification)"""
        
        # Purchasing behavior
        if (duration >= self.behavior_rules['purchasing']['min_duration'] and
            num_stops >= self.behavior_rules['purchasing']['min_stops']):
            return 'purchasing'
        
        # Window shopping
        if (self.behavior_rules['window_shopping']['min_duration'] <= duration <= 
            self.behavior_rules['window_shopping']['max_duration']):
            return 'window_shopping'
        
        # Browsing
        if (duration >= self.behavior_rules['browsing']['min_duration'] and
            num_stops >= self.behavior_rules['browsing']['min_stops']):
            return 'browsing'
        
        # Idle/Loitering
        if stationary_time >= self.behavior_rules['idle']['min_stationary_time']:
            return 'idle'
        
        # Passing through
        if (duration <= self.behavior_rules['passing_through']['max_duration'] or
            num_stops <= self.behavior_rules['passing_through']['max_stops']):
            return 'passing_through'
        
        return 'browsing'  # Default
    
    def _identify_zones(self, positions: List) -> List[str]:
        """
        Identify which zones the person visited (simplified, coordinate-based).
        This is separate from the config-based ZoneDetector used with Track.
        """
        zones = set()
        
        for pos in positions:
            if len(pos) >= 2:
                x, y = pos[0], pos[1]
                
                # Example zones (you should adjust these based on your setup)
                if x < 200:
                    zones.add('entrance')
                elif x > 1000:
                    zones.add('exit')
                elif 400 < x < 600 and 300 < y < 500:
                    zones.add('checkout')
                else:
                    zones.add('shopping_area')
        
        return list(zones)

    # ---------------- UPDATED SUMMARY (SAFE, NO KeyError) ---------------- #

    def generate_summary(self, analyzed_tracks: List[Dict]) -> Dict[str, Any]:
        """
        Generate summary statistics from analyzed tracks
        
        Combines:
        - Original metrics (total_visitors, conversion_rate, etc.)
        - New safe handling of missing 'duration'
        - Extra behavior distribution info
        """
        try:
            if not analyzed_tracks:
                return {
                    "total_visitors": 0,
                    "total_customers": 0,
                    "window_shoppers": 0,
                    "browsers": 0,
                    "purchasers": 0,
                    "passing_through": 0,
                    "idle": 0,
                    "conversion_rate": 0.0,
                    "avg_visit_duration": 0.0,
                    "total_checkout_visitors": 0,
                    "behavior_distribution": {}
                }
            
            total_visitors = len(analyzed_tracks)

            # ---- Safe durations (no KeyError: 'duration') ----
            durations: List[float] = []
            for t in analyzed_tracks:
                d = t.get("duration", None)
                if d is None:
                    d = t.get("visit_duration", 0.0)
                try:
                    durations.append(float(d))
                except (ValueError, TypeError):
                    durations.append(0.0)
            avg_duration = float(np.mean(durations)) if durations else 0.0

            # ---- Normalize behavior labels ----
            normalized_behaviors: List[str] = []
            for t in analyzed_tracks:
                b = t.get("behavior", "unknown")
                if isinstance(b, BehaviorType):
                    b = b.value
                elif not isinstance(b, str):
                    b = str(b)
                normalized_behaviors.append(b)

            behavior_counts = Counter(normalized_behaviors)

            # ---- Purchasers / checkout visitors ----
            purchasers = 0
            total_checkout_visitors = 0

            for t, b in zip(analyzed_tracks, normalized_behaviors):
                visited_checkout_flag = bool(t.get("visited_checkout", False))
                zones = t.get("zones_visited", []) or []
                if "checkout" in zones:
                    visited_checkout_flag = True

                made_purchase_flag = bool(t.get("made_purchase", False))
                # Treat purchasing behavior OR checkout visit OR explicit made_purchase
                if (b == BehaviorType.PURCHASING.value or
                    made_purchase_flag or
                    visited_checkout_flag):
                    purchasers += 1

                if visited_checkout_flag:
                    total_checkout_visitors += 1

            # ---- Other behavior-specific counts (keep old semantics) ----
            window_shoppers = behavior_counts.get(BehaviorType.WINDOW_SHOPPING.value, 0)
            browsers = behavior_counts.get(BehaviorType.BROWSING.value, 0)
            passing_through = behavior_counts.get(BehaviorType.PASSING_THROUGH.value, 0)
            idle = behavior_counts.get(BehaviorType.IDLE.value, 0)

            conversion_rate = (purchasers / total_visitors * 100) if total_visitors > 0 else 0.0

            return {
                "total_visitors": total_visitors,
                "total_customers": purchasers,
                "window_shoppers": window_shoppers,
                "browsers": browsers,
                "purchasers": purchasers,
                "passing_through": passing_through,
                "idle": idle,
                "conversion_rate": round(conversion_rate, 2),
                "avg_visit_duration": round(avg_duration, 2),
                "total_checkout_visitors": total_checkout_visitors,
                "behavior_distribution": dict(behavior_counts)
            }

        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            import traceback
            traceback.print_exc()
            
            # Return safe defaults
            return {
                "total_visitors": len(analyzed_tracks) if analyzed_tracks else 0,
                "total_customers": 0,
                "window_shoppers": 0,
                "browsers": 0,
                "purchasers": 0,
                "passing_through": 0,
                "idle": 0,
                "conversion_rate": 0.0,
                "avg_visit_duration": 0.0,
                "total_checkout_visitors": 0,
                "behavior_distribution": {}
            }

    # ---------------- NEW: BUSINESS INSIGHTS ---------------- #

    def get_insights(self, analyzed_tracks: List[Dict]) -> Dict[str, Any]:
        """
        Generate business insights from analyzed tracks based on summary stats.
        """
        try:
            summary = self.generate_summary(analyzed_tracks)
            
            insights = {
                'summary': summary,
                'recommendations': []
            }
            
            # Low conversion rate
            if summary['conversion_rate'] < 20:
                insights['recommendations'].append({
                    'type': 'conversion',
                    'message': 'Low conversion rate detected. Consider improving product placement or checkout process.'
                })
            
            # High idle count
            if summary['total_visitors'] > 0 and summary['idle'] > summary['total_visitors'] * 0.2:
                insights['recommendations'].append({
                    'type': 'engagement',
                    'message': 'High number of idle visitors. Consider adding more engaging displays or staff assistance.'
                })
            
            # Many passing through
            if summary['total_visitors'] > 0 and summary['passing_through'] > summary['total_visitors'] * 0.4:
                insights['recommendations'].append({
                    'type': 'attention',
                    'message': 'Many visitors passing through. Consider improving store entrance appeal.'
                })
            
            return insights
            
        except Exception as e:
            print(f"❌ Error generating insights: {e}")
            return {
                'summary': self.generate_summary(analyzed_tracks),
                'recommendations': []
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
