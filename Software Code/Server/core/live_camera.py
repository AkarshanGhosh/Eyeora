"""
Live Camera System - Complete Version with Weapon Detection Only
Includes: Person detection, pose estimation, clothing classification, behavior tracking,
          object detection, AND weapon-only threat detection
Location: Software Code/Server/core/live_camera_abnormal.py
"""

import cv2
import numpy as np
import time
from typing import List, Dict, Optional, Tuple
from collections import deque

try:
    from core.detection_engine import EnhancedDetectionEngine
except Exception:
    EnhancedDetectionEngine = None

from core.tracker import PersonTracker, Detection
from core.alert_system import AlertSystem


class PoseEstimator:
    """Estimates human pose using YOLO pose model"""

    def __init__(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO("yolo11n-pose.pt")
            self.enabled = True
            print("✅ Pose estimation enabled")
        except Exception as e:
            print(f"⚠️ Pose estimation not available: {e}")
            self.enabled = False

    def estimate_pose(self, image: np.ndarray) -> List[Dict]:
        """Estimate poses in image"""
        if not self.enabled:
            return []

        try:
            results = self.model(image, verbose=False, imgsz=640)[0]
            poses: List[Dict] = []

            if hasattr(results, "keypoints") and results.keypoints is not None:
                for keypoints in results.keypoints:
                    if keypoints.xy is not None:
                        kpts = keypoints.xy[0].cpu().numpy()
                        conf = (
                            keypoints.conf[0].cpu().numpy()
                            if getattr(keypoints, "conf", None) is not None
                            else None
                        )

                        activity = self._classify_activity(kpts)

                        poses.append(
                            {
                                "keypoints": kpts,
                                "confidence": conf,
                                "activity": activity,
                            }
                        )

            return poses
        except Exception:
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
        except Exception:
            return "unknown"


class ClothingClassifier:
    """Simple clothing color classifier"""
    
    COLOR_RANGES = {
        "red": ([0, 100, 100], [10, 255, 255]),
        "blue": ([100, 100, 100], [130, 255, 255]),
        "green": ([40, 100, 100], [80, 255, 255]),
        "yellow": ([20, 100, 100], [40, 255, 255]),
        "black": ([0, 0, 0], [180, 255, 50]),
        "white": ([0, 0, 200], [180, 30, 255]),
        "orange": ([10, 100, 100], [20, 255, 255]),
        "purple": ([130, 100, 100], [160, 255, 255]),
    }

    def classify_clothing(self, person_crop: np.ndarray) -> Dict:
        if person_crop is None or person_crop.size == 0:
            return {"color": "unknown", "pattern": "unknown"}

        try:
            h, w = person_crop.shape[:2]
            if h > 200:
                scale = 200 / h
                person_crop = cv2.resize(person_crop, None, fx=scale, fy=scale)
                h, w = person_crop.shape[:2]

            upper_body = person_crop[: int(h * 0.4), :]
            dominant_color = self._get_dominant_color(upper_body)
            return {"color": dominant_color, "pattern": "solid"}
        except Exception:
            return {"color": "unknown", "pattern": "unknown"}

    def _get_dominant_color(self, image: np.ndarray) -> str:
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            sample_size = min(1000, image.shape[0] * image.shape[1])
            if sample_size <= 0:
                return "unknown"

            indices = np.random.choice(image.shape[0] * image.shape[1], sample_size, replace=False)
            hsv_flat = hsv.reshape(-1, 3)
            hsv_sample = hsv_flat[indices]

            color_counts = {}
            for color_name, (lower, upper) in self.COLOR_RANGES.items():
                mask = cv2.inRange(hsv_sample, np.array(lower), np.array(upper))
                color_counts[color_name] = int(cv2.countNonZero(mask))

            dominant = max(color_counts, key=color_counts.get)
            if color_counts[dominant] < sample_size * 0.1:
                return "mixed"
            return dominant
        except Exception:
            return "unknown"


class LivePerson:
    """Live tracked person container"""
    
    def __init__(self, track_id: int):
        self.track_id = track_id
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.positions = deque(maxlen=50)
        self.activities = deque(maxlen=15)
        self.clothing: Optional[Dict] = None
        self.detected_objects = set()

    def update(self, position: Tuple[float, float], pose: Optional[Dict] = None, clothing: Optional[Dict] = None):
        self.last_seen = time.time()
        self.positions.append(position)

        if pose:
            if "activity" in pose:
                self.activities.append(pose["activity"])

        if clothing and self.clothing is None:
            self.clothing = clothing

    def add_nearby_object(self, object_name: str):
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


class _FallbackEnhancedDetectionEngine:
    """Minimal fallback if EnhancedDetectionEngine not available"""
    
    def __init__(self, model_name="yolo11n.pt", confidence_threshold=0.5, device=None, enable_abnormality=True):
        from core.detection_engine import DetectionEngine
        self.base = DetectionEngine(model_name=model_name, confidence_threshold=confidence_threshold, device=device)
        self.enable_abnormality = enable_abnormality

    def detect_all_objects(self, image: np.ndarray, classes: Optional[List[int]] = None) -> List[Detection]:
        return self.base.detect_all_objects(image, classes=classes)

    def detect_with_abnormality(self, image: np.ndarray, detect_poses: bool = False):
        dets = self.base.detect_all_objects(image, classes=None)
        normal = [{"detection": d, "bbox": d.bbox, "class_name": d.class_name, "abnormality": None} for d in dets]
        abnormal = []
        return normal, abnormal


class LiveCameraSystem:
    """Live camera system with weapon-only threat detection"""
    
    def __init__(
        self,
        camera_index: int = 0,
        enable_pose: bool = True,
        enable_clothing: bool = True,
        enable_tracking: bool = True,
        enable_objects: bool = True,
        enable_abnormality: bool = True,
    ):
        self.camera_index = camera_index
        self.camera = None

        if EnhancedDetectionEngine is None:
            self.detection_engine = _FallbackEnhancedDetectionEngine(
                model_name="yolo11n.pt",
                confidence_threshold=0.5,
                device=None,
                enable_abnormality=enable_abnormality,
            )
        else:
            self.detection_engine = EnhancedDetectionEngine(
                model_name="yolo11n.pt",
                confidence_threshold=0.5,
                device=None,
                enable_abnormality=enable_abnormality,
            )

        self.tracker = PersonTracker() if enable_tracking else None

        self.object_classes = [0, 39, 43, 63, 67]

        self.pose_estimator = PoseEstimator() if enable_pose else None
        self.clothing_classifier = ClothingClassifier() if enable_clothing else None

        self.live_persons: Dict[int, LivePerson] = {}
        self.detected_objects: List[Detection] = []

        self.alert_system = AlertSystem()

        self.show_abnormality = enable_abnormality
        self.abnormal_detections = deque(maxlen=200)
        self.alert_cooldown: Dict[str, float] = {}
        self.total_threats = 0

        self.fps = 0.0
        self.frame_count = 0
        self.start_time = time.time()
        self.last_fps_time = time.time()
        self.fps_frame_count = 0

        self.show_detections = True
        self.show_pose = enable_pose
        self.show_clothing = enable_clothing
        self.show_tracking = enable_tracking
        self.show_stats = True
        self.show_objects = enable_objects

        self.is_running = False
        self.current_frame = None
        self.processed_frame = None
        self.skip_pose_frames = 0
        self.skip_clothing_frames = 0

        print("✅ Complete Live Camera System initialized")
        print(f"   Pose: {'ON' if enable_pose else 'OFF'}")
        print(f"   Clothing: {'ON' if enable_clothing else 'OFF'}")
        print(f"   Objects: {'ON' if enable_objects else 'OFF'}")
        print(f"   Weapon Detection: {'ON' if enable_abnormality else 'OFF'}")

    def start(self) -> bool:
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                print(f"❌ Could not open camera {self.camera_index}")
                return False

            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            self.is_running = True
            self.start_time = time.time()
            self.last_fps_time = time.time()

            print(f"✅ Camera {self.camera_index} started (640x480 @ 30fps)")
            return True
        except Exception as e:
            print(f"❌ Camera start error: {e}")
            return False

    def stop(self):
        self.is_running = False
        if self.camera:
            self.camera.release()
        print("⏹️ Camera stopped")

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.camera or not self.is_running:
            return False, None

        ret, frame = self.camera.read()
        if ret:
            self.current_frame = frame.copy()
            self.frame_count += 1
        return ret, frame

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        timestamp = time.time()
        processed = frame.copy()

        abnormal_detections: List[Dict] = []
        if self.show_abnormality and hasattr(self.detection_engine, "detect_with_abnormality"):
            normal_dicts, abnormal_dicts = self.detection_engine.detect_with_abnormality(frame, detect_poses=False)

            all_detections: List[Detection] = []
            for d in normal_dicts:
                if "detection" in d and isinstance(d["detection"], Detection):
                    all_detections.append(d["detection"])
            for d in abnormal_dicts:
                if "detection" in d and isinstance(d["detection"], Detection):
                    all_detections.append(d["detection"])
                    abnormal_detections.append(d)
                    self.total_threats += 1

                    ab = d.get("abnormality", {}) or {}
                    self.abnormal_detections.append(
                        {
                            "timestamp": timestamp,
                            "type": ab.get("type", "unknown"),
                            "class": d.get("class_name", "unknown"),
                            "confidence": float(ab.get("confidence", 0.0)),
                        }
                    )
        else:
            all_detections = self.detection_engine.detect_all_objects(frame, classes=self.object_classes)

        person_detections = [d for d in all_detections if d.class_name == "person"]
        object_detections = [d for d in all_detections if d.class_name != "person"]
        self.detected_objects = object_detections

        poses: List[Dict] = []
        if self.pose_estimator and self.show_pose:
            self.skip_pose_frames += 1
            if self.skip_pose_frames >= 3:
                poses = self.pose_estimator.estimate_pose(frame)
                self.skip_pose_frames = 0

        if self.tracker:
            tracks = self.tracker.update(person_detections, timestamp)

            crops: List[np.ndarray] = []
            if self.clothing_classifier and self.show_clothing:
                self.skip_clothing_frames += 1
                if self.skip_clothing_frames >= 5:
                    for det in person_detections:
                        x1, y1, x2, y2 = map(int, det.bbox)
                        crops.append(frame[y1:y2, x1:x2])
                    self.skip_clothing_frames = 0

            self._update_live_persons(tracks, poses, crops, object_detections)

        self._handle_alerts(abnormal_detections)

        if self.show_detections:
            processed = self._draw_visualizations_with_abnormality(
                processed,
                person_detections,
                object_detections,
                poses,
                abnormal_detections,
            )

        if self.show_stats:
            weapons_count = len(abnormal_detections)
            processed = self._draw_stats(processed, len(person_detections), len(object_detections), weapons_count)

        self.fps_frame_count += 1
        if timestamp - self.last_fps_time >= 1.0:
            self.fps = self.fps_frame_count / (timestamp - self.last_fps_time)
            self.fps_frame_count = 0
            self.last_fps_time = timestamp

        self.processed_frame = processed
        return processed

    def _update_live_persons(self, tracks, poses, crops, objects):
        current_ids = set()

        for i, track in enumerate(tracks):
            tid = track.track_id
            current_ids.add(tid)

            if tid not in self.live_persons:
                self.live_persons[tid] = LivePerson(tid)

            person = self.live_persons[tid]
            position = track.last_position
            pose = poses[i] if i < len(poses) else None

            clothing = None
            if self.clothing_classifier and crops and i < len(crops) and person.clothing is None:
                clothing = self.clothing_classifier.classify_clothing(crops[i])

            if position:
                person.update(position, pose, clothing)

            if position and objects:
                px, py = position
                for obj in objects:
                    ox1, oy1, ox2, oy2 = obj.bbox
                    if abs(px - (ox1 + ox2) / 2) < 100 and abs(py - (oy1 + oy2) / 2) < 100:
                        person.add_nearby_object(obj.class_name)

        to_remove = [
            tid for tid, p in self.live_persons.items()
            if tid not in current_ids and time.time() - p.last_seen > 3.0
        ]
        for tid in to_remove:
            del self.live_persons[tid]

    def _handle_alerts(self, abnormal_detections: List[Dict]):
        """Trigger alerts for weapons with cooldown"""
        now = time.time()
        cooldown_sec = 5.0

        for det_dict in abnormal_detections:
            weapon_class = det_dict.get("class_name", "weapon")
            abnormality_type = det_dict.get("abnormality", {}).get("type", "weapon_detected")
            confidence = float(det_dict.get("abnormality", {}).get("confidence", 0.5))

            key = f"{weapon_class}:{abnormality_type}"
            last = self.alert_cooldown.get(key, 0.0)
            if now - last < cooldown_sec:
                continue

            self.alert_cooldown[key] = now

            try:
                if hasattr(self.alert_system, "trigger_alert"):
                    self.alert_system.trigger_alert(
                        alert_type=abnormality_type,
                        message=f"Weapon detected: {weapon_class}",
                        confidence=confidence,
                    )
                elif hasattr(self.alert_system, "raise_alert"):
                    self.alert_system.raise_alert(
                        abnormality_type,
                        f"Weapon detected: {weapon_class}",
                        confidence,
                    )
                elif hasattr(self.alert_system, "notify"):
                    self.alert_system.notify(
                        f"Weapon detected: {weapon_class}",
                        confidence,
                    )
                else:
                    print(f"⚠ ALERT: {weapon_class} detected (conf {confidence:.2f})")
            except Exception as e:
                print(f"⚠ AlertSystem error: {e}")

    def _draw_visualizations_with_abnormality(
        self,
        frame: np.ndarray,
        person_detections: List[Detection],
        object_detections: List[Detection],
        poses: List[Dict],
        abnormal_detections: List[Dict],
    ) -> np.ndarray:
        """Draw people (green), objects (orange), weapons (red)"""
        
        for det in person_detections:
            x1, y1, x2, y2 = map(int, det.bbox)

            track_id_label = None
            activity_label = None
            clothing_label = None

            if self.tracker:
                for track in self.tracker.tracks:
                    if not track.is_active or not track.last_position:
                        continue
                    tx, ty = track.last_position
                    if x1 <= tx <= x2 and y1 <= ty <= y2:
                        track_id_label = track.track_id
                        lp = self.live_persons.get(track.track_id)
                        if lp:
                            activity_label = lp.dominant_activity if lp.dominant_activity != "unknown" else None
                            if lp.clothing and lp.clothing.get("color") not in (None, "unknown"):
                                clothing_label = lp.clothing["color"]
                        break

            color = (0, 255, 0)
            thickness = 2
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

            labels = []
            if track_id_label is not None:
                labels.append(f"ID:{track_id_label}")
            if activity_label:
                labels.append(activity_label)
            if clothing_label:
                labels.append(clothing_label)

            if not labels:
                labels.append(f"person {det.confidence:.2f}")

            y = y1 - 6
            for text in labels:
                fs = 0.45
                ft = 1
                (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fs, ft)
                y0 = max(0, y - h - 6)
                cv2.rectangle(frame, (x1, y0), (x1 + w + 6, y), color, -1)
                cv2.putText(frame, text, (x1 + 3, y - 3), cv2.FONT_HERSHEY_SIMPLEX, fs, (255, 255, 255), ft)
                y = y0 - 4

        if self.show_objects:
            for det in object_detections:
                x1, y1, x2, y2 = map(int, det.bbox)

                color = (255, 165, 0)
                thickness = 2

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                label = f"{det.class_name} {det.confidence:.2f}"
                cv2.putText(frame, label, (x1, max(0, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        for det_dict in abnormal_detections:
            x1, y1, x2, y2 = map(int, det_dict["bbox"])
            
            color = (0, 0, 255)
            thickness = 3
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            weapon_class = det_dict.get("class_name", "weapon")
            confidence = det_dict.get("confidence", 0.0)
            label = f"⚠ {weapon_class} {confidence:.2f}"
            
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - h - 6), (x1 + w, y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.putText(frame, "⚠", (x2 - 30, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        if self.show_pose and poses:
            for pose in poses:
                if "keypoints" in pose:
                    self._draw_pose_keypoints(frame, pose["keypoints"], (0, 255, 255))

        return frame

    def _draw_pose_keypoints(self, frame: np.ndarray, keypoints: np.ndarray, color=(0, 255, 255)):
        skeleton = [
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
            (5, 11), (6, 12), (11, 12),
            (11, 13), (13, 15), (12, 14), (14, 16)
        ]

        for x, y in keypoints:
            if x > 0 and y > 0:
                cv2.circle(frame, (int(x), int(y)), 3, color, -1)

        for a, b in skeleton:
            if a < len(keypoints) and b < len(keypoints):
                p1, p2 = keypoints[a], keypoints[b]
                if p1[0] > 0 and p1[1] > 0 and p2[0] > 0 and p2[1] > 0:
                    cv2.line(frame, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), color, 2)

    def _draw_stats(self, frame: np.ndarray, people_count: int, objects_count: int, weapons_count: int) -> np.ndarray:
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (5, 5), (210, 140), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

        stats = [
            f"FPS: {self.fps:.1f}",
            f"People: {people_count}",
            f"Objects: {objects_count}",
            f"Tracked: {len(self.live_persons)}",
            f"WEAPONS: {weapons_count}",
            f"Total weapons: {self.total_threats}",
        ]

        y = 25
        for s in stats:
            col = (0, 0, 255) if "WEAPON" in s else (255, 255, 255)
            cv2.putText(frame, s, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1)
            y += 20

        if weapons_count > 0:
            cv2.rectangle(frame, (w - 120, 10), (w - 10, 55), (0, 0, 255), -1)
            cv2.putText(frame, "⚠ ALERT", (w - 110, 42),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return frame

    def get_statistics(self) -> Dict:
        return {
            "fps": self.fps,
            "frame_count": self.frame_count,
            "people_detected": len(self.live_persons),
            "objects_detected": len(self.detected_objects),
            "total_threats": self.total_threats,
            "active_threats": len([d for d in self.abnormal_detections if time.time() - d["timestamp"] < 5.0]),
            "running_time": time.time() - self.start_time,
            "live_persons": [
                {
                    "id": p.track_id,
                    "duration": p.duration,
                    "activity": p.dominant_activity,
                    "clothing": p.clothing,
                    "is_moving": p.is_moving,
                    "nearby_objects": list(p.detected_objects),
                }
                for p in self.live_persons.values()
            ],
            "objects": [{"class": o.class_name, "confidence": o.confidence, "bbox": o.bbox} for o in self.detected_objects],
            "recent_threats": list(self.abnormal_detections)[-10:],
        }

    def toggle_detections(self):
        self.show_detections = not self.show_detections
        return self.show_detections

    def toggle_pose(self):
        if self.pose_estimator:
            self.show_pose = not self.show_pose
            return self.show_pose
        return False

    def toggle_objects(self):
        self.show_objects = not self.show_objects
        return self.show_objects

    def toggle_stats(self):
        self.show_stats = not self.show_stats
        return self.show_stats

    def toggle_abnormality(self):
        self.show_abnormality = not self.show_abnormality
        return self.show_abnormality

    def run(self, window_name: str = "Eyeora Live (Weapon Detection)"):
        if not self.start():
            return

        print("🎛 Controls: [q]=quit  [d]=detections  [p]=pose  [o]=objects  [s]=stats  [a]=abnormality")
        try:
            while self.is_running:
                ok, frame = self.read_frame()
                if not ok or frame is None:
                    continue

                out = self.process_frame(frame)
                cv2.imshow(window_name, out)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("d"):
                    print("Detections:", self.toggle_detections())
                elif key == ord("p"):
                    print("Pose:", self.toggle_pose())
                elif key == ord("o"):
                    print("Objects:", self.toggle_objects())
                elif key == ord("s"):
                    print("Stats:", self.toggle_stats())
                elif key == ord("a"):
                    print("Abnormality:", self.toggle_abnormality())
        finally:
            self.stop()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    print("✅ Complete Live Camera System with Weapon Detection Ready")
    print("🎥 Features:")
    print("  - Real-time person detection (GREEN boxes)")
    print("  - Multi-object detection")
    print("  - Multi-person tracking")
    print("  - Pose estimation")
    print("  - Clothing color classification")
    print("  - Activity recognition")
    print("  - Weapon-only detection (RED boxes)")

    system = LiveCameraSystem(
        camera_index=0,
        enable_pose=True,
        enable_clothing=True,
        enable_tracking=True,
        enable_objects=True,
        enable_abnormality=True,
    )
    system.run()