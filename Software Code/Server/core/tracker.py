"""
Advanced Person Tracking System using YOLO + ByteTrack
Tracks individuals throughout their store visit
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from datetime import datetime
import uuid


@dataclass
class Detection:
    """Single detection from YOLO"""
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str
    
    @property
    def center(self) -> Tuple[float, float]:
        """Get center point of bounding box"""
        return ((self.bbox[0] + self.bbox[2]) / 2, 
                (self.bbox[1] + self.bbox[3]) / 2)
    
    @property
    def area(self) -> float:
        """Get area of bounding box"""
        return (self.bbox[2] - self.bbox[0]) * (self.bbox[3] - self.bbox[1])


@dataclass
class Track:
    """Tracked person throughout video"""
    track_id: int
    uuid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    detections: List[Detection] = field(default_factory=list)
    positions: List[Tuple[float, float]] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    frames: List[int] = field(default_factory=list)
    
    # Status
    is_active: bool = True
    entry_time: Optional[float] = None
    exit_time: Optional[float] = None
    entry_frame: Optional[int] = None
    exit_frame: Optional[int] = None
    
    # Behavior tracking
    visited_zones: List[str] = field(default_factory=list)
    behavior_history: List[str] = field(default_factory=list)
    idle_duration: float = 0.0
    
    # Purchase detection
    visited_checkout: bool = False
    made_purchase: bool = False
    
    # Age tracking
    frames_without_detection: int = 0
    total_frames: int = 0
    
    def update(self, detection: Detection, frame_num: int, timestamp: float):
        """Update track with new detection"""
        self.detections.append(detection)
        self.positions.append(detection.center)
        self.timestamps.append(timestamp)
        self.frames.append(frame_num)
        self.frames_without_detection = 0
        self.total_frames += 1
        
        if self.entry_time is None:
            self.entry_time = timestamp
            self.entry_frame = frame_num
    
    def mark_lost(self):
        """Mark track as lost (no detection for several frames)"""
        self.frames_without_detection += 1
    
    def mark_exited(self, timestamp: float, frame_num: int):
        """Mark person as exited"""
        self.is_active = False
        self.exit_time = timestamp
        self.exit_frame = frame_num
    
    @property
    def duration(self) -> float:
        """Get duration of visit in seconds"""
        if self.entry_time and self.exit_time:
            return self.exit_time - self.entry_time
        elif self.timestamps:
            return self.timestamps[-1] - self.timestamps[0]
        return 0.0
    
    @property
    def last_position(self) -> Optional[Tuple[float, float]]:
        """Get last known position"""
        return self.positions[-1] if self.positions else None
    
    @property
    def movement_distance(self) -> float:
        """Calculate total movement distance"""
        if len(self.positions) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(self.positions)):
            x1, y1 = self.positions[i-1]
            x2, y2 = self.positions[i]
            distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            total_distance += distance
        
        return total_distance
    
    @property
    def is_stationary(self) -> bool:
        """Check if person is standing still"""
        if len(self.positions) < 10:
            return False
        
        recent_positions = self.positions[-10:]
        x_coords = [p[0] for p in recent_positions]
        y_coords = [p[1] for p in recent_positions]
        
        x_variance = np.var(x_coords)
        y_variance = np.var(y_coords)
        
        return x_variance < 50 and y_variance < 50  # Threshold for stationary


class PersonTracker:
    """
    Multi-object tracking system for people
    Simplified ByteTrack-like approach
    """
    
    def __init__(self, max_age: int = 30, min_hits: int = 3, iou_threshold: float = 0.3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        
        self.tracks: List[Track] = []
        self.next_track_id = 1
        self.frame_count = 0
    
    def update(self, detections: List[Detection], timestamp: float) -> List[Track]:
        """
        Update tracks with new detections
        
        Args:
            detections: List of person detections from current frame
            timestamp: Current timestamp in seconds
            
        Returns:
            List of active tracks
        """
        self.frame_count += 1
        
        # Filter only person detections
        person_detections = [d for d in detections if d.class_name == "person"]
        
        if len(self.tracks) == 0:
            # Initialize tracks for first frame
            for detection in person_detections:
                self._create_track(detection, timestamp)
        else:
            # Match detections to existing tracks
            self._match_detections_to_tracks(person_detections, timestamp)
        
        # Remove old tracks
        self._remove_old_tracks()
        
        return [t for t in self.tracks if t.is_active]
    
    def _create_track(self, detection: Detection, timestamp: float):
        """Create new track"""
        track = Track(track_id=self.next_track_id)
        track.update(detection, self.frame_count, timestamp)
        self.tracks.append(track)
        self.next_track_id += 1
    
    def _match_detections_to_tracks(self, detections: List[Detection], timestamp: float):
        """Match detections to existing tracks using IoU"""
        
        # Calculate IoU matrix
        iou_matrix = np.zeros((len(self.tracks), len(detections)))
        
        for t_idx, track in enumerate(self.tracks):
            if not track.is_active:
                continue
            
            last_detection = track.detections[-1] if track.detections else None
            if last_detection is None:
                continue
            
            for d_idx, detection in enumerate(detections):
                iou = self._calculate_iou(last_detection.bbox, detection.bbox)
                iou_matrix[t_idx, d_idx] = iou
        
        # Hungarian algorithm simplified - greedy matching
        matched_tracks = set()
        matched_detections = set()
        
        # Match in order of highest IoU
        while True:
            max_iou = 0
            max_track = -1
            max_detection = -1
            
            for t_idx in range(len(self.tracks)):
                if t_idx in matched_tracks:
                    continue
                for d_idx in range(len(detections)):
                    if d_idx in matched_detections:
                        continue
                    if iou_matrix[t_idx, d_idx] > max_iou:
                        max_iou = iou_matrix[t_idx, d_idx]
                        max_track = t_idx
                        max_detection = d_idx
            
            if max_iou < self.iou_threshold:
                break
            
            # Match found
            self.tracks[max_track].update(detections[max_detection], 
                                         self.frame_count, timestamp)
            matched_tracks.add(max_track)
            matched_detections.add(max_detection)
        
        # Mark unmatched tracks as lost
        for t_idx, track in enumerate(self.tracks):
            if t_idx not in matched_tracks and track.is_active:
                track.mark_lost()
        
        # Create new tracks for unmatched detections
        for d_idx, detection in enumerate(detections):
            if d_idx not in matched_detections:
                self._create_track(detection, timestamp)
    
    def _calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate Intersection over Union"""
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2
        
        # Intersection
        x_min = max(x1_min, x2_min)
        y_min = max(y1_min, y2_min)
        x_max = min(x1_max, x2_max)
        y_max = min(y1_max, y2_max)
        
        if x_max < x_min or y_max < y_min:
            return 0.0
        
        intersection = (x_max - x_min) * (y_max - y_min)
        
        # Union
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _remove_old_tracks(self):
        """Remove tracks that haven't been detected for too long"""
        current_time = self.timestamps[-1] if hasattr(self, 'timestamps') else 0
        
        for track in self.tracks:
            if track.frames_without_detection > self.max_age:
                if track.is_active and track.total_frames >= self.min_hits:
                    track.mark_exited(current_time, self.frame_count)
    
    def get_all_tracks(self) -> List[Track]:
        """Get all tracks including completed ones"""
        return self.tracks
    
    def get_active_tracks(self) -> List[Track]:
        """Get only active tracks"""
        return [t for t in self.tracks if t.is_active]
    
    def get_completed_tracks(self) -> List[Track]:
        """Get completed tracks"""
        return [t for t in self.tracks if not t.is_active and t.total_frames >= self.min_hits]


if __name__ == "__main__":
    print("✅ Person Tracker Module Ready")
    print("📊 Features: Multi-object tracking, behavior analysis, zone detection")