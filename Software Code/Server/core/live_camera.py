"""
Live Camera System - Optimized for 30+ FPS with Multi-Object Detection
Includes: Person detection, pose estimation, clothing classification, behavior tracking, object detection
Location: Software Code/Server/core/live_camera.py
"""

import cv2
import numpy as np
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import deque
import threading
from queue import Queue

from core.detection_engine import DetectionEngine
from core.tracker import PersonTracker, Detection
from core.behavior_analyzer import BehaviorAnalyzer
from core.alert_system import AlertSystem
from core.config import CONFIDENCE_THRESHOLD


class PoseEstimator:
    """
    Estimates human pose using YOLO pose model
    """
    
    def __init__(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO('yolo11n-pose.pt')  # Using nano for speed
            self.enabled = True
            print("✅ Pose estimation enabled")
        except Exception as e:
            print(f"⚠️ Pose estimation not available: {e}")
            self.enabled = False
    
    def estimate_pose(self, image: np.ndarray, skip_frames: int = 2) -> List[Dict]:
        """Estimate poses in image (optimized)"""
        if not self.enabled:
            return []
        
        try:
            # Run with optimized settings
            results = self.model(image, verbose=False, imgsz=640)[0]
            poses = []
            
            if hasattr(results, 'keypoints') and results.keypoints is not None:
                for keypoints in results.keypoints:
                    if keypoints.xy is not None:
                        kpts = keypoints.xy[0].cpu().numpy()
                        conf = keypoints.conf[0].cpu().numpy() if keypoints.conf is not None else None
                        
                        poses.append({
                            'keypoints': kpts,
                            'confidence': conf,
                            'activity': self._classify_activity(kpts)
                        })
            
            return poses
        except Exception as e:
            return []
    
    def _classify_activity(self, keypoints: np.ndarray) -> str:
        """Classify activity based on keypoints"""
        try:
            if len(keypoints) < 17:
                return "unknown"
            
            nose = keypoints[0]
            left_shoulder = keypoints[5]
            right_shoulder = keypoints[6]
            left_hip = keypoints[11]
            right_hip = keypoints[12]
            
            if nose[1] < left_hip[1]:
                shoulder_center = (left_shoulder[1] + right_shoulder[1]) / 2
                hip_center = (left_hip[1] + right_hip[1]) / 2
                
                if abs(shoulder_center - hip_center) < 50:
                    return "sitting"
                elif nose[1] < shoulder_center:
                    return "standing"
                else:
                    return "bending"
            
            return "moving"
            
        except:
            return "unknown"


class ClothingClassifier:
    """
    Classifies clothing colors and types (Optimized)
    """
    
    COLOR_RANGES = {
        'red': ([0, 100, 100], [10, 255, 255]),
        'blue': ([100, 100, 100], [130, 255, 255]),
        'green': ([40, 100, 100], [80, 255, 255]),
        'yellow': ([20, 100, 100], [40, 255, 255]),
        'black': ([0, 0, 0], [180, 255, 50]),
        'white': ([0, 0, 200], [180, 30, 255]),
        'orange': ([10, 100, 100], [20, 255, 255]),
        'purple': ([130, 100, 100], [160, 255, 255]),
    }
    
    def classify_clothing(self, person_crop: np.ndarray) -> Dict:
        """Classify clothing color (optimized)"""
        if person_crop is None or person_crop.size == 0:
            return {'color': 'unknown', 'pattern': 'unknown'}
        
        try:
            h, w = person_crop.shape[:2]
            
            # Resize for faster processing
            if h > 200:
                scale = 200 / h
                person_crop = cv2.resize(person_crop, None, fx=scale, fy=scale)
                h, w = person_crop.shape[:2]
            
            # Focus on upper body
            upper_body = person_crop[:int(h * 0.4), :]
            
            # Get dominant color
            dominant_color = self._get_dominant_color(upper_body)
            
            return {
                'color': dominant_color,
                'pattern': 'solid'
            }
            
        except:
            return {'color': 'unknown', 'pattern': 'unknown'}
    
    def _get_dominant_color(self, image: np.ndarray) -> str:
        """Get dominant color name (optimized)"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Sample pixels instead of full image
            sample_size = min(1000, image.shape[0] * image.shape[1])
            indices = np.random.choice(image.shape[0] * image.shape[1], sample_size, replace=False)
            hsv_flat = hsv.reshape(-1, 3)
            hsv_sample = hsv_flat[indices]
            
            color_counts = {}
            for color_name, (lower, upper) in self.COLOR_RANGES.items():
                mask = cv2.inRange(hsv_sample, np.array(lower), np.array(upper))
                count = cv2.countNonZero(mask)
                color_counts[color_name] = count
            
            dominant = max(color_counts, key=color_counts.get)
            
            if color_counts[dominant] < sample_size * 0.1:
                return 'mixed'
            
            return dominant
            
        except:
            return 'unknown'


class LivePerson:
    """Extended person info for live tracking"""
    
    def __init__(self, track_id: int):
        self.track_id = track_id
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.positions = deque(maxlen=50)  # Reduced for performance
        self.poses = deque(maxlen=15)
        self.clothing = None
        self.activities = deque(maxlen=15)
        self.behaviors = []
        self.detected_objects = set()  # Objects near this person
        
    def update(self, position: Tuple[float, float], pose: Dict = None, clothing: Dict = None):
        """Update person info"""
        self.last_seen = time.time()
        self.positions.append(position)
        
        if pose:
            self.poses.append(pose)
            if 'activity' in pose:
                self.activities.append(pose['activity'])
        
        if clothing and not self.clothing:
            self.clothing = clothing
    
    def add_nearby_object(self, object_name: str):
        """Add detected object near person"""
        self.detected_objects.add(object_name)
    
    @property
    def duration(self) -> float:
        return self.last_seen - self.first_seen
    
    @property
    def dominant_activity(self) -> str:
        if not self.activities:
            return "unknown"
        return max(set(self.activities), key=list(self.activities).count)
    
    @property
    def is_moving(self) -> bool:
        if len(self.positions) < 5:
            return False
        
        recent = list(self.positions)[-5:]
        x_var = np.var([p[0] for p in recent])
        y_var = np.var([p[1] for p in recent])
        
        return x_var > 50 or y_var > 50


class LiveCameraSystem:
    """
    Optimized live camera system for 30+ FPS with multi-object detection
    """
    
    def __init__(
        self,
        camera_index: int = 0,
        enable_pose: bool = False,  # Disabled by default for performance
        enable_clothing: bool = True,
        enable_tracking: bool = True,
        enable_objects: bool = True
    ):
        """Initialize live camera system"""
        self.camera_index = camera_index
        self.camera = None
        
        # Detection and tracking
        self.detection_engine = DetectionEngine()
        self.tracker = PersonTracker() if enable_tracking else None
        
        # Advanced features
        self.pose_estimator = PoseEstimator() if enable_pose else None
        self.clothing_classifier = ClothingClassifier() if enable_clothing else None
        
        # Live persons tracking
        self.live_persons: Dict[int, LivePerson] = {}
        self.detected_objects: List[Dict] = []  # Current frame objects
        
        # Alert system
        self.alert_system = AlertSystem()
        
        # Stats
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        self.last_fps_time = time.time()
        self.fps_frame_count = 0
        
        # Display settings
        self.show_detections = True
        self.show_pose = enable_pose
        self.show_clothing = enable_clothing
        self.show_tracking = enable_tracking
        self.show_stats = True
        self.show_objects = enable_objects
        
        # Processing
        self.is_running = False
        self.current_frame = None
        self.processed_frame = None
        
        # Performance optimization
        self.skip_pose_frames = 0
        self.skip_clothing_frames = 0
        self.process_every_n_frames = 1  # Process every frame for real-time
        
        print("✅ Live Camera System initialized (Optimized)")
        print(f"   Pose: {'ON' if enable_pose else 'OFF (disabled for performance)'}")
        print(f"   Objects: {'ON' if enable_objects else 'OFF'}")
    
    def start(self) -> bool:
        """Start camera capture"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                print(f"❌ Could not open camera {self.camera_index}")
                return False
            
            # Optimize camera settings for speed
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Lower resolution for speed
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer
            
            self.is_running = True
            self.start_time = time.time()
            self.last_fps_time = time.time()
            
            print(f"✅ Camera {self.camera_index} started (640x480 @ 30fps)")
            return True
            
        except Exception as e:
            print(f"❌ Camera start error: {e}")
            return False
    
    def stop(self):
        """Stop camera capture"""
        self.is_running = False
        if self.camera:
            self.camera.release()
        print("⏹️ Camera stopped")
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read frame from camera"""
        if not self.camera or not self.is_running:
            return False, None
        
        ret, frame = self.camera.read()
        if ret:
            self.current_frame = frame.copy()
            self.frame_count += 1
        
        return ret, frame
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Process frame with all detections (OPTIMIZED)
        """
        timestamp = time.time()
        processed = frame.copy()
        
        # 1. ALL OBJECT DETECTION (People + Objects in one pass)
        all_detections = self.detection_engine.detect_all_objects(
            frame,
            classes=None  # Detect all classes
        )
        
        # Separate people and objects
        person_detections = [d for d in all_detections if d.class_name == "person"]
        object_detections = [d for d in all_detections if d.class_name != "person"]
        
        self.detected_objects = object_detections
        
        # 2. POSE ESTIMATION (Skip frames for performance)
        poses = []
        if self.pose_estimator and self.show_pose:
            self.skip_pose_frames += 1
            if self.skip_pose_frames >= 3:  # Only every 3rd frame
                poses = self.pose_estimator.estimate_pose(frame)
                self.skip_pose_frames = 0
        
        # 3. TRACKING
        if self.tracker:
            active_tracks = self.tracker.update(person_detections, timestamp)
            
            # Get crops only if needed
            crops = []
            if self.clothing_classifier and self.show_clothing:
                self.skip_clothing_frames += 1
                if self.skip_clothing_frames >= 5:  # Only every 5th frame
                    for det in person_detections:
                        x1, y1, x2, y2 = map(int, det.bbox)
                        crop = frame[y1:y2, x1:x2]
                        crops.append(crop)
                    self.skip_clothing_frames = 0
            
            # Update live persons
            self._update_live_persons(active_tracks, poses, crops, object_detections)
        
        # 4. VISUALIZE (if enabled)
        if self.show_detections:
            processed = self._draw_visualizations(
                processed, person_detections, object_detections, poses
            )
        
        # 5. DRAW STATS
        if self.show_stats:
            processed = self._draw_stats(processed, len(person_detections), len(object_detections))
        
        # Calculate FPS (more accurate)
        self.fps_frame_count += 1
        if timestamp - self.last_fps_time >= 1.0:
            self.fps = self.fps_frame_count / (timestamp - self.last_fps_time)
            self.fps_frame_count = 0
            self.last_fps_time = timestamp
        
        self.processed_frame = processed
        return processed
    
    def _update_live_persons(self, tracks, poses, crops, objects):
        """Update live persons tracking"""
        current_ids = set()
        
        for i, track in enumerate(tracks):
            track_id = track.track_id
            current_ids.add(track_id)
            
            if track_id not in self.live_persons:
                self.live_persons[track_id] = LivePerson(track_id)
            
            person = self.live_persons[track_id]
            position = track.last_position
            pose = poses[i] if i < len(poses) else None
            
            # Get clothing only if available
            clothing = None
            if self.clothing_classifier and crops and i < len(crops) and person.clothing is None:
                clothing = self.clothing_classifier.classify_clothing(crops[i])
            
            person.update(position, pose, clothing)
            
            # Find nearby objects
            if position and objects:
                px, py = position
                for obj in objects:
                    ox1, oy1, ox2, oy2 = obj.bbox
                    # Check if object is near person (within 100px)
                    if abs(px - (ox1 + ox2) / 2) < 100 and abs(py - (oy1 + oy2) / 2) < 100:
                        person.add_nearby_object(obj.class_name)
        
        # Remove old persons
        to_remove = [tid for tid, p in self.live_persons.items() 
                     if tid not in current_ids and time.time() - p.last_seen > 3.0]
        for tid in to_remove:
            del self.live_persons[tid]
    
    def _draw_visualizations(
        self,
        frame: np.ndarray,
        person_detections: List[Detection],
        object_detections: List[Detection],
        poses: List[Dict]
    ) -> np.ndarray:
        """Draw all visualizations (OPTIMIZED)"""
        
        # Draw person detections
        for i, detection in enumerate(person_detections):
            x1, y1, x2, y2 = map(int, detection.bbox)
            
            # Bounding box (thinner for speed)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
            
            # Get person info
            person_info = []
            if self.tracker:
                for track in self.tracker.tracks:
                    if track.is_active and track.last_position:
                        tx, ty = track.last_position
                        if x1 <= tx <= x2 and y1 <= ty <= y2:
                            person_info.append(f"ID:{track.track_id}")
                            
                            if track.track_id in self.live_persons:
                                live_person = self.live_persons[track.track_id]
                                
                                if live_person.dominant_activity != "unknown":
                                    person_info.append(f"{live_person.dominant_activity}")
                                
                                if live_person.clothing and live_person.clothing.get('color') != 'unknown':
                                    person_info.append(f"{live_person.clothing['color']}")
                            break
            
            # Draw info (smaller font for speed)
            if person_info:
                y_offset = y1 - 5
                for info in person_info:
                    cv2.putText(frame, info, (x1, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                    y_offset -= 15
            else:
                cv2.putText(frame, f"P {detection.confidence:.2f}", (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # Draw object detections
        if self.show_objects:
            for detection in object_detections:
                x1, y1, x2, y2 = map(int, detection.bbox)
                
                # Different color for objects
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 165, 0), 1)  # Orange
                
                label = f"{detection.class_name} {detection.confidence:.2f}"
                cv2.putText(frame, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 165, 0), 1)
        
        # Draw pose (if enabled)
        if self.show_pose and poses:
            for pose in poses:
                if 'keypoints' in pose:
                    self._draw_pose_keypoints(frame, pose['keypoints'])
        
        return frame
    
    def _draw_pose_keypoints(self, frame: np.ndarray, keypoints: np.ndarray):
        """Draw pose keypoints (simplified for speed)"""
        skeleton = [
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
            (5, 11), (6, 12), (11, 12),
            (11, 13), (13, 15), (12, 14), (14, 16)
        ]
        
        # Draw keypoints (smaller)
        for x, y in keypoints:
            if x > 0 and y > 0:
                cv2.circle(frame, (int(x), int(y)), 2, (0, 255, 255), -1)
        
        # Draw skeleton (thinner)
        for start_idx, end_idx in skeleton:
            if start_idx < len(keypoints) and end_idx < len(keypoints):
                start = keypoints[start_idx]
                end = keypoints[end_idx]
                if start[0] > 0 and start[1] > 0 and end[0] > 0 and end[1] > 0:
                    cv2.line(frame, (int(start[0]), int(start[1])),
                            (int(end[0]), int(end[1])), (0, 255, 255), 1)
    
    def _draw_stats(self, frame: np.ndarray, people_count: int, objects_count: int) -> np.ndarray:
        """Draw statistics (OPTIMIZED)"""
        h, w = frame.shape[:2]
        
        # Smaller overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (5, 5), (150, 85), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.8, overlay, 0.2, 0)
        
        # Stats text (smaller)
        stats = [
            f"FPS: {self.fps:.1f}",
            f"People: {people_count}",
            f"Objects: {objects_count}",
            f"Tracked: {len(self.live_persons)}"
        ]
        
        y_offset = 20
        for stat in stats:
            cv2.putText(frame, stat, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            y_offset += 18
        
        return frame
    
    def get_statistics(self) -> Dict:
        """Get current statistics"""
        return {
            "fps": self.fps,
            "frame_count": self.frame_count,
            "people_detected": len(self.live_persons),
            "objects_detected": len(self.detected_objects),
            "running_time": time.time() - self.start_time,
            "live_persons": [
                {
                    "id": person.track_id,
                    "duration": person.duration,
                    "activity": person.dominant_activity,
                    "clothing": person.clothing,
                    "is_moving": person.is_moving,
                    "nearby_objects": list(person.detected_objects)
                }
                for person in self.live_persons.values()
            ],
            "objects": [
                {
                    "class": obj.class_name,
                    "confidence": obj.confidence,
                    "bbox": obj.bbox
                }
                for obj in self.detected_objects
            ]
        }
    
    def toggle_detections(self):
        """Toggle detection visualization"""
        self.show_detections = not self.show_detections
        return self.show_detections
    
    def toggle_pose(self):
        """Toggle pose visualization"""
        if self.pose_estimator:
            self.show_pose = not self.show_pose
            return self.show_pose
        return False
    
    def toggle_objects(self):
        """Toggle object visualization"""
        self.show_objects = not self.show_objects
        return self.show_objects
    
    def toggle_stats(self):
        """Toggle stats display"""
        self.show_stats = not self.show_stats
        return self.show_stats


if __name__ == "__main__":
    print("✅ Live Camera System Module Ready (Optimized)")
    print("🎥 Features:")
    print("  - Real-time person detection (30+ FPS)")
    print("  - Multi-object detection (80 classes)")
    print("  - Multi-person tracking")
    print("  - Pose estimation (optional)")
    print("  - Clothing classification")
    print("  - Activity recognition")
    print("  - Nearby object detection")