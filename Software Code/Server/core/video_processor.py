"""
Complete Video Processing Engine - Eyeora AI-CCTV
------------------------------------------------
Location: Software Code/Server/core/video_processor.py

This module provides a complete pipeline for:
- Person detection (YOLO)
- Multi-person tracking (PersonTracker)
- Behavior analysis (BehaviorAnalyzer + zones)
- Optional pose estimation (YOLO pose) + threatening pose detection
- Clothing color classification
- Object detection (non-person objects)
- Abnormality/threat detection (EnhancedDetectionEngine abnormality detector)
- Red/Green box visualization
- CSV export via DataExporter
- Text report export

IMPORTANT:
- This file also guarantees compatibility with:
      from core.video_processor import VideoProcessor
  by exporting VideoProcessor as an alias of CompleteVideoProcessor at the bottom.

Requirements:
- ultralytics installed
- core/config.py defines key constants
- core/tracker.py defines Detection, Track, PersonTracker
- core/behavior_analyzer.py defines BehaviorAnalyzer and draw_zones
- core/csv_exporter.py defines DataExporter
- core/detection_engine.py defines EnhancedDetectionEngine (your new version)

Notes:
- The code tries to be robust even if some features are missing (pose model not available, etc).
"""

from __future__ import annotations

import cv2
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from collections import Counter

# YOLO pose uses ultralytics
try:
    from ultralytics import YOLO
except Exception:
    YOLO = None  # type: ignore


# ------------------------------------------------------------
# Core imports (your project modules)
# ------------------------------------------------------------
from core.config import (
    MODEL_PATH,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    VIDEO_FPS_PROCESS,
    VIDEO_OUTPUT_FPS,
    PROCESSED_DIR,
    YOLO_MODEL,
    MODELS_DIR,
)

from core.tracker import PersonTracker, Detection, Track
from core.behavior_analyzer import BehaviorAnalyzer, draw_zones
from core.csv_exporter import DataExporter

# IMPORTANT: your detection_engine.py now contains EnhancedDetectionEngine
# If you still have an old DetectionEngine in some files, keep it separate.
from core.detection_engine import EnhancedDetectionEngine


# ============================================================
# Pose Estimator (Video)
# ============================================================

class PoseEstimatorVideo:
    """
    Pose estimation wrapper for video.

    Uses a YOLO pose model if available.
    The goal is not perfect activity recognition—just stable heuristics.
    """

    def __init__(self, model_name: str = "yolo11n-pose.pt", imgsz: int = 640):
        self.model_name = model_name
        self.imgsz = imgsz
        self.enabled = False
        self.model = None

        if YOLO is None:
            print("⚠️ ultralytics not installed, pose disabled")
            return

        try:
            self.model = YOLO(self.model_name)
            self.enabled = True
            print("✅ Pose estimation enabled for video")
        except Exception as e:
            print(f"⚠️ Pose estimation not available: {e}")
            self.enabled = False

    def estimate_pose(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Estimate poses in image.

        Returns:
            [
              {
                'keypoints': np.ndarray shape (17,2),
                'confidence': np.ndarray shape (17,) or None,
                'activity': str,
                'is_threat': bool,
                'threat_type': str
              }, ...
            ]
        """
        if not self.enabled or self.model is None:
            return []

        try:
            results = self.model(image, verbose=False, imgsz=self.imgsz)[0]
            poses: List[Dict[str, Any]] = []

            if hasattr(results, "keypoints") and results.keypoints is not None:
                for keypoints in results.keypoints:
                    if keypoints.xy is not None:
                        kpts = keypoints.xy[0].cpu().numpy()  # (17,2)
                        conf = None
                        if getattr(keypoints, "conf", None) is not None:
                            conf = keypoints.conf[0].cpu().numpy()

                        activity = self._classify_activity(kpts)
                        threat = self._check_threatening_pose(kpts)

                        poses.append(
                            {
                                "keypoints": kpts,
                                "confidence": conf,
                                "activity": activity,
                                "is_threat": threat.get("is_threat", False),
                                "threat_type": threat.get("reason", "none"),
                                "threat_confidence": threat.get("confidence", 0.0),
                            }
                        )
            return poses
        except Exception:
            return []

    def _classify_activity(self, keypoints: np.ndarray) -> str:
        """
        Very simple activity classification.
        """
        try:
            if len(keypoints) < 17:
                return "unknown"

            nose = keypoints[0]
            left_shoulder = keypoints[5]
            right_shoulder = keypoints[6]
            left_hip = keypoints[11]
            right_hip = keypoints[12]

            shoulder_center_y = (left_shoulder[1] + right_shoulder[1]) / 2
            hip_center_y = (left_hip[1] + right_hip[1]) / 2

            # If nose exists and is above hip center: likely upright
            if nose[1] < hip_center_y:
                # standing vs sitting/bending heuristic
                if abs(shoulder_center_y - hip_center_y) < 50:
                    return "sitting"
                if nose[1] < shoulder_center_y:
                    return "standing"
                return "bending"
            return "moving"
        except Exception:
            return "unknown"

    def _check_threatening_pose(self, keypoints: np.ndarray) -> Dict[str, Any]:
        """
        Detect threatening pose from keypoints (heuristics).
        """
        try:
            if len(keypoints) < 17:
                return {"is_threat": False, "reason": "insufficient_data", "confidence": 0.0}

            left_wrist = keypoints[9]
            right_wrist = keypoints[10]
            left_elbow = keypoints[7]
            right_elbow = keypoints[8]
            left_shoulder = keypoints[5]
            right_shoulder = keypoints[6]

            # Pointing/aiming gesture heuristic
            right_arm_extended = (
                right_wrist[0] > right_elbow[0]
                and abs(right_wrist[1] - right_shoulder[1]) < 100
            )
            left_arm_extended = (
                left_wrist[0] < left_elbow[0]
                and abs(left_wrist[1] - left_shoulder[1]) < 100
            )

            if right_arm_extended or left_arm_extended:
                return {"is_threat": True, "reason": "pointing_gesture", "confidence": 0.7}

            # Hands raised
            both_hands_up = (
                left_wrist[1] < left_shoulder[1]
                and right_wrist[1] < right_shoulder[1]
            )
            if both_hands_up:
                return {"is_threat": True, "reason": "hands_raised", "confidence": 0.5}

            return {"is_threat": False, "reason": "normal_pose", "confidence": 0.0}
        except Exception:
            return {"is_threat": False, "reason": "detection_error", "confidence": 0.0}


# ============================================================
# Clothing Classifier (Video)
# ============================================================

class ClothingClassifierVideo:
    """
    Simple clothing color classifier using HSV masking.
    Focuses on upper body region.
    """

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

    def classify_clothing(self, person_crop: np.ndarray) -> Dict[str, str]:
        """
        Returns {color: ..., pattern: ...}
        """
        if person_crop is None or person_crop.size == 0:
            return {"color": "unknown", "pattern": "unknown"}

        try:
            h, w = person_crop.shape[:2]
            if h <= 0 or w <= 0:
                return {"color": "unknown", "pattern": "unknown"}

            # Resize large crops to speed up
            if h > 240:
                scale = 240 / h
                person_crop = cv2.resize(person_crop, None, fx=scale, fy=scale)
                h, w = person_crop.shape[:2]

            # Upper body heuristic: top 40%
            upper_body = person_crop[: int(h * 0.4), :]

            dominant_color = self._get_dominant_color(upper_body)
            return {"color": dominant_color, "pattern": "solid"}
        except Exception:
            return {"color": "unknown", "pattern": "unknown"}

    def _get_dominant_color(self, image: np.ndarray) -> str:
        """
        Find dominant color bucket from predefined HSV ranges.
        """
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # sample pixels
            total_pixels = image.shape[0] * image.shape[1]
            if total_pixels <= 0:
                return "unknown"

            sample_size = min(1500, total_pixels)
            idx = np.random.choice(total_pixels, sample_size, replace=False)
            hsv_flat = hsv.reshape(-1, 3)
            hsv_sample = hsv_flat[idx]

            color_counts = {}
            for color_name, (lower, upper) in self.COLOR_RANGES.items():
                lower_np = np.array(lower, dtype=np.uint8)
                upper_np = np.array(upper, dtype=np.uint8)
                mask = cv2.inRange(hsv_sample, lower_np, upper_np)
                color_counts[color_name] = int(cv2.countNonZero(mask))

            dominant = max(color_counts, key=color_counts.get)
            if color_counts[dominant] < int(sample_size * 0.10):
                return "mixed"
            return dominant
        except Exception:
            return "unknown"


# ============================================================
# Complete Video Processor
# ============================================================

class CompleteVideoProcessor:
    """
    Complete video processor with ALL features:

    - Person detection and tracking
    - Behavior analysis
    - Optional pose estimation + threatening pose detection
    - Optional clothing classification
    - Optional object detection
    - Optional abnormality/threat detection with red/green boxes
    - CSV export
    - Text report export

    This is meant to replace/upgrade old VideoProcessor safely.
    """

    def __init__(
        self,
        model_path: str = None,
        show_zones: bool = True,
        enable_pose: bool = True,
        enable_clothing: bool = True,
        enable_objects: bool = True,
        enable_abnormality: bool = True,
        confidence_threshold: float = None,
    ):
        self.model_path = model_path or MODEL_PATH
        self.show_zones = show_zones
        self.enable_pose = enable_pose
        self.enable_clothing = enable_clothing
        self.enable_objects = enable_objects
        self.enable_abnormality = enable_abnormality

        # Use provided confidence else config default
        self.confidence_threshold = (
            float(confidence_threshold) if confidence_threshold is not None else float(CONFIDENCE_THRESHOLD)
        )

        print("🚀 Initializing Complete Video Processor...")
        print(f"   Zones: {'ON' if show_zones else 'OFF'}")
        print(f"   Pose: {'ON' if enable_pose else 'OFF'}")
        print(f"   Clothing: {'ON' if enable_clothing else 'OFF'}")
        print(f"   Objects: {'ON' if enable_objects else 'OFF'}")
        print(f"   Abnormality: {'ON' if enable_abnormality else 'OFF'}")

        # Detection engine (your new enhanced abnormality engine)
        self.detection_engine = EnhancedDetectionEngine(
            model_name=YOLO_MODEL,
            confidence_threshold=self.confidence_threshold,
            iou_threshold=float(IOU_THRESHOLD),
            enable_abnormality=enable_abnormality,
        )

        # Pose estimator
        self.pose_estimator = PoseEstimatorVideo() if enable_pose else None

        # Clothing classifier
        self.clothing_classifier = ClothingClassifierVideo() if enable_clothing else None

        # Tracking & analysis (initialized per video)
        self.tracker: Optional[PersonTracker] = None
        self.analyzer: Optional[BehaviorAnalyzer] = None

        # Exporter
        self.exporter = DataExporter()

        # Per-track enrichment caches
        self.track_clothing: Dict[int, Dict[str, str]] = {}
        self.track_poses: Dict[int, List[Dict[str, Any]]] = {}
        self.track_activities: Dict[int, List[str]] = {}

        # Abnormality / threats timeline
        self.abnormal_frames: List[Dict[str, Any]] = []
        self.frame_classifications: List[Dict[str, Any]] = []
        self.total_threats: int = 0

    # --------------------------------------------------------
    # Public: process_video
    # --------------------------------------------------------
    def process_video(
        self,
        video_path: str,
        output_path: str = None,
        generate_output_video: bool = True,
        export_csv: bool = True,
        export_report: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a full video.

        Returns:
            {
              success: bool,
              video_info: {...},
              output_video_path: str|None,
              csv_path: str|None,
              report_path: str|None,
              total_tracks: int,
              summary: {...},
              processing_time: float,
              analyzed_tracks: [...],
              abnormal_frames: [...],
            }
        """
        start_time = time.time()
        video_path_p = Path(video_path)

        if not video_path_p.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        cap = cv2.VideoCapture(str(video_path_p))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration = (frame_count / fps) if fps > 0 else 0.0

        video_info = {
            "filename": video_path_p.name,
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": duration,
        }

        print("\n" + "=" * 70)
        print("🎥 COMPLETE VIDEO PROCESSING STARTED")
        print("=" * 70)
        print(f"📹 Video: {video_info['filename']}")
        print(f"📊 Resolution: {width}x{height}")
        print(f"⏱️  Duration: {duration:.2f}s ({frame_count} frames @ {fps:.2f} fps)")
        print(f"⚙️  Processing step: every {VIDEO_FPS_PROCESS} frame(s)")
        print("=" * 70)

        # init tracker/analyzer
        self.tracker = PersonTracker(max_age=30, min_hits=3, iou_threshold=0.3)
        self.analyzer = BehaviorAnalyzer(width, height, fps)

        # reset caches
        self.track_clothing.clear()
        self.track_poses.clear()
        self.track_activities.clear()
        self.abnormal_frames.clear()
        self.frame_classifications.clear()
        self.total_threats = 0

        # output video writer
        output_writer = None
        output_path_p: Optional[Path] = None
        if generate_output_video:
            if output_path is None:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path_p = PROCESSED_DIR / "videos" / f"processed_{ts}.mp4"
            else:
                output_path_p = Path(output_path)

            output_path_p.parent.mkdir(parents=True, exist_ok=True)

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            output_writer = cv2.VideoWriter(
                str(output_path_p),
                fourcc,
                float(VIDEO_OUTPUT_FPS),
                (width, height),
            )
            print(f"🎬 Output video: {output_path_p}")

        frame_num = 0
        processed_frames = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_num += 1
            timestamp = (frame_num / fps) if fps > 0 else float(frame_num)

            # process every Nth frame
            if VIDEO_FPS_PROCESS > 1 and (frame_num % int(VIDEO_FPS_PROCESS) != 0):
                continue

            processed_frames += 1

            annotated, frame_data = self._process_single_frame(
                frame=frame,
                frame_num=frame_num,
                timestamp=timestamp,
                width=width,
                height=height,
            )

            self.frame_classifications.append(frame_data)

            if frame_data.get("abnormal_count", 0) > 0:
                self.abnormal_frames.append(
                    {
                        "frame_num": frame_num,
                        "timestamp": timestamp,
                        "abnormal_count": frame_data["abnormal_count"],
                        "abnormalities": frame_data.get("abnormalities", []),
                    }
                )
                self.total_threats += int(frame_data["abnormal_count"])

            if output_writer is not None:
                output_writer.write(annotated)

            if processed_frames % 50 == 0 and frame_count > 0:
                progress = (frame_num / frame_count) * 100.0
                tracks_count = len(self.tracker.tracks) if self.tracker else 0
                print(f"⏳ Progress: {progress:.1f}% | Tracks: {tracks_count} | Threats: {self.total_threats}")

        cap.release()
        if output_writer is not None:
            output_writer.release()

        # analyze tracks
        analyzed_tracks = self._analyze_complete_tracks()

        # behavior summary + abnormal summary
        behavior_summary = self.analyzer.generate_summary(analyzed_tracks) if self.analyzer else {}
        abnormal_summary = self._generate_abnormality_summary()

        complete_summary = {**behavior_summary, **abnormal_summary}

        # print summary
        self._print_complete_summary(complete_summary, video_info)

        # export CSV
        csv_path = None
        if export_csv and analyzed_tracks:
            try:
                csv_path = self.exporter.export_to_csv(analyzed_tracks, include_summary=True)
                print(f"💾 CSV exported: {csv_path}")
            except Exception as e:
                print(f"⚠️ CSV export failed: {e}")

        # export report
        report_path = None
        if export_report:
            try:
                # save report next to output video if possible else next to input
                report_base = output_path_p if output_path_p else (video_path_p.parent / video_path_p.stem)
                report_path = self._export_complete_report(complete_summary, video_info, Path(str(report_base)))
            except Exception as e:
                print(f"⚠️ Report export failed: {e}")

        elapsed = time.time() - start_time
        print("\n" + "=" * 70)
        print(f"✅ PROCESSING COMPLETED in {elapsed:.2f}s")
        print("=" * 70)

        return {
            "success": True,
            "video_info": video_info,
            "output_video_path": str(output_path_p) if output_path_p else None,
            "csv_path": csv_path,
            "report_path": report_path,
            "total_tracks": len(analyzed_tracks),
            "summary": complete_summary,
            "processing_time": elapsed,
            "analyzed_tracks": analyzed_tracks,
            "abnormal_frames": self.abnormal_frames,
        }

    # --------------------------------------------------------
    # Public: process_image
    # --------------------------------------------------------
    def process_image(self, image_path: str, output_path: str = None) -> Dict[str, Any]:
        """
        Process a single image with abnormality detection + pose + annotation.
        Returns a dict similar to your earlier interface.
        """
        image_path_p = Path(image_path)
        if not image_path_p.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        frame = cv2.imread(str(image_path_p))
        if frame is None:
            raise ValueError("Could not read image")

        poses: List[Dict[str, Any]] = []
        if self.enable_pose and self.pose_estimator:
            poses = self.pose_estimator.estimate_pose(frame)

        if self.enable_abnormality:
            normal_detections, abnormal_detections = self.detection_engine.detect_with_abnormality(
                frame, confidence=self.confidence_threshold, detect_poses=False
            )
        else:
            # fallback: treat everything as normal
            normal_detections, abnormal_detections = self.detection_engine.detect_with_abnormality(
                frame, confidence=self.confidence_threshold, detect_poses=False
            )
            abnormal_detections = []

        annotated = self.detection_engine.visualize_with_abnormality(
            frame,
            normal_detections=normal_detections,
            abnormal_detections=abnormal_detections,
            show_confidence=True,
            thickness=2,
        )

        # overlay pose keypoints
        if poses:
            for pose in poses:
                if "keypoints" in pose:
                    color = (0, 0, 255) if pose.get("is_threat") else (0, 255, 255)
                    self._draw_pose_keypoints(annotated, pose["keypoints"], color)

        if output_path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path_p = PROCESSED_DIR / "images" / f"detected_{ts}.jpg"
        else:
            output_path_p = Path(output_path)

        output_path_p.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path_p), annotated)

        has_pose_threat = any(p.get("is_threat", False) for p in poses)
        has_threats = (len(abnormal_detections) > 0) or has_pose_threat

        return {
            "success": True,
            "normal_count": len(normal_detections),
            "abnormal_count": len(abnormal_detections),
            "poses_detected": len(poses),
            "threatening_poses": sum(1 for p in poses if p.get("is_threat")),
            "output_path": str(output_path_p),
            "has_threats": has_threats,
            "abnormalities": [
                {
                    "type": det.get("abnormality", {}).get("type", "unknown"),
                    "class": det.get("class_name", "unknown"),
                    "confidence": det.get("abnormality", {}).get("confidence", det.get("confidence", 0.0)),
                }
                for det in abnormal_detections
            ],
        }

    # ========================================================
    # Internals
    # ========================================================

    def _process_single_frame(
        self,
        frame: np.ndarray,
        frame_num: int,
        timestamp: float,
        width: int,
        height: int,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Per-frame processing with:
        - detect objects (+ abnormal)
        - tracking (persons)
        - clothing capture per track
        - pose capture per track (best-effort mapping)
        - annotate
        """
        annotated = frame.copy()

        # 1) detect objects
        if self.enable_abnormality:
            normal_detections, abnormal_detections = self.detection_engine.detect_with_abnormality(
                frame, confidence=self.confidence_threshold, detect_poses=False
            )
            # flatten list of Detection for tracking/objects
            all_dets: List[Detection] = [d["detection"] for d in normal_detections] + [d["detection"] for d in abnormal_detections]
        else:
            normal_detections, abnormal_detections = self.detection_engine.detect_with_abnormality(
                frame, confidence=self.confidence_threshold, detect_poses=False
            )
            abnormal_detections = []
            all_dets = [d["detection"] for d in normal_detections]

        person_detections = [d for d in all_dets if d.class_name == "person"]
        object_detections = [d for d in all_dets if d.class_name != "person"]

        # 2) pose
        poses: List[Dict[str, Any]] = []
        if self.enable_pose and self.pose_estimator:
            poses = self.pose_estimator.estimate_pose(frame)

        # 3) update tracker
        if self.tracker is None:
            self.tracker = PersonTracker(max_age=30, min_hits=3, iou_threshold=0.3)
        active_tracks: List[Track] = self.tracker.update(person_detections, timestamp)

        # 4) clothing (once per track)
        if self.enable_clothing and self.clothing_classifier:
            for tr in active_tracks:
                if tr.track_id in self.track_clothing:
                    continue
                if not tr.detections:
                    continue
                bbox = tr.detections[-1].bbox
                x1, y1, x2, y2 = map(int, bbox)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(width - 1, x2), min(height - 1, y2)
                crop = frame[y1:y2, x1:x2]
                clothing = self.clothing_classifier.classify_clothing(crop)
                self.track_clothing[tr.track_id] = clothing

        # 5) store pose per track (best-effort mapping by index)
        # NOTE: pose model and tracker do not guarantee same ordering.
        # For now we map by track index which works in many simple scenes.
        for idx, tr in enumerate(active_tracks):
            if idx >= len(poses):
                break
            self.track_poses.setdefault(tr.track_id, []).append(poses[idx])
            self.track_activities.setdefault(tr.track_id, []).append(poses[idx].get("activity", "unknown"))

        # 6) annotate
        annotated = self._annotate_complete_frame(
            frame=annotated,
            tracks=active_tracks,
            objects=object_detections,
            poses=poses,
            normal_detections=normal_detections,
            abnormal_detections=abnormal_detections,
            frame_num=frame_num,
            timestamp=timestamp,
        )

        frame_data = {
            "frame_num": frame_num,
            "timestamp": timestamp,
            "person_count": len(person_detections),
            "object_count": len(object_detections),
            "abnormal_count": len(abnormal_detections),
            "abnormalities": [
                {
                    "type": det.get("abnormality", {}).get("type", "unknown"),
                    "class": det.get("class_name", "unknown"),
                    "confidence": det.get("abnormality", {}).get("confidence", det.get("confidence", 0.0)),
                }
                for det in abnormal_detections
            ],
        }

        return annotated, frame_data

    def _annotate_complete_frame(
        self,
        frame: np.ndarray,
        tracks: List[Track],
        objects: List[Detection],
        poses: List[Dict[str, Any]],
        normal_detections: List[Dict[str, Any]],
        abnormal_detections: List[Dict[str, Any]],
        frame_num: int,
        timestamp: float,
    ) -> np.ndarray:
        """
        Draw zones + tracks + objects + pose keypoints.
        Green for normal tracks, red for abnormal/threat tracks.
        """
        if self.show_zones and self.analyzer:
            frame = draw_zones(frame, self.analyzer.zone_detector)

        # ---- tracks
        for i, track in enumerate(tracks):
            if not track.detections:
                continue

            bbox = track.detections[-1].bbox
            x1, y1, x2, y2 = map(int, bbox)

            # threat flags
            is_abnormal = False
            abnormality_info = ""

            # match abnormal detections by near bbox
            for ab in abnormal_detections:
                abx1, aby1, abx2, aby2 = map(int, ab["bbox"])
                if abs(x1 - abx1) < 12 and abs(y1 - aby1) < 12:
                    is_abnormal = True
                    abnormality_info = ab.get("abnormality", {}).get("type", "abnormal")
                    break

            # pose threat
            if i < len(poses) and poses[i].get("is_threat", False):
                is_abnormal = True
                abnormality_info = poses[i].get("threat_type", "threat_pose")

            color = (0, 0, 255) if is_abnormal else (0, 255, 0)
            thickness = 3 if is_abnormal else 2

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

            # labels
            labels: List[str] = []
            if is_abnormal:
                labels.append(f"ABNORMAL: {abnormality_info}")
            else:
                labels.append("Normal")

            labels.append(f"ID: {track.track_id}")

            if track.track_id in self.track_clothing:
                c = self.track_clothing[track.track_id]
                if c.get("color") and c["color"] != "unknown":
                    labels.append(f"Cloth: {c['color']}")

            if track.track_id in self.track_activities and self.track_activities[track.track_id]:
                acts = self.track_activities[track.track_id]
                dominant = max(set(acts), key=acts.count)
                if dominant != "unknown":
                    labels.append(f"Act: {dominant}")

            # draw label stack
            y_offset = y1 - 5
            for label in labels:
                font_scale = 0.55 if "ABNORMAL" in label else 0.45
                font_thickness = 2 if "ABNORMAL" in label else 1

                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)
                cv2.rectangle(frame, (x1, y_offset - th - 5), (x1 + tw + 2, y_offset), color, -1)
                cv2.putText(frame, label, (x1 + 1, y_offset - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), font_thickness)
                y_offset -= (th + 8)

            # trajectory
            if hasattr(track, "positions") and track.positions and len(track.positions) > 1:
                pts = track.positions[-30:]
                pts = [(int(p[0]), int(p[1])) for p in pts]
                for j in range(1, len(pts)):
                    cv2.line(frame, pts[j - 1], pts[j], color, 2)

        # ---- objects
        if self.enable_objects:
            for obj in objects:
                x1, y1, x2, y2 = map(int, obj.bbox)
                threat_objects = ["knife", "scissors", "weapon", "gun", "pistol", "rifle"]
                is_threat = any(t in obj.class_name.lower() for t in threat_objects)
                ocolor = (0, 0, 255) if is_threat else (255, 165, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), ocolor, 2)
                label = f"{'⚠ ' if is_threat else ''}{obj.class_name}"
                cv2.putText(frame, label, (x1, y1 - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, ocolor, 1)

        # ---- pose keypoints
        if self.enable_pose and poses:
            for pose in poses:
                if "keypoints" in pose:
                    pcolor = (0, 0, 255) if pose.get("is_threat") else (0, 255, 255)
                    self._draw_pose_keypoints(frame, pose["keypoints"], pcolor)

        # ---- overlay info
        overlay = [
            f"Frame {frame_num} | {timestamp:.1f}s",
            f"Tracks: {len(tracks)}",
            f"Threats: {len(abnormal_detections)}",
        ]
        oy = 28
        for t in overlay:
            cv2.putText(frame, t, (10, oy), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            oy += 25

        return frame

    def _draw_pose_keypoints(self, frame: np.ndarray, keypoints: np.ndarray, color=(0, 255, 255)) -> None:
        """
        Draw keypoints + skeleton lines.
        """
        skeleton = [
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
            (5, 11), (6, 12), (11, 12),
            (11, 13), (13, 15), (12, 14), (14, 16),
        ]

        # points
        for x, y in keypoints:
            if x > 0 and y > 0:
                cv2.circle(frame, (int(x), int(y)), 3, color, -1)

        # lines
        for a, b in skeleton:
            if a < len(keypoints) and b < len(keypoints):
                p1 = keypoints[a]
                p2 = keypoints[b]
                if p1[0] > 0 and p1[1] > 0 and p2[0] > 0 and p2[1] > 0:
                    cv2.line(frame, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), color, 2)

    def _analyze_complete_tracks(self) -> List[Dict[str, Any]]:
        """
        Merge:
        - BehaviorAnalyzer track analysis
        - clothing info
        - dominant activity
        - pose threat counts
        """
        if self.tracker is None or self.analyzer is None:
            return []

        all_tracks = self.tracker.get_completed_tracks()
        analyzed: List[Dict[str, Any]] = []

        for tr in all_tracks:
            base = self.analyzer.analyze_track(tr)

            # clothing
            base["clothing"] = self.track_clothing.get(tr.track_id, {"color": "unknown", "pattern": "unknown"})

            # activity
            acts = self.track_activities.get(tr.track_id, [])
            if acts:
                base["dominant_activity"] = max(set(acts), key=acts.count)
                base["activity_history"] = acts[-20:]
            else:
                base["dominant_activity"] = "unknown"
                base["activity_history"] = []

            # pose threats
            poses = self.track_poses.get(tr.track_id, [])
            threat_poses = [p for p in poses if p.get("is_threat", False)]
            base["threat_pose_count"] = len(threat_poses)
            base["had_threatening_pose"] = len(threat_poses) > 0

            analyzed.append(base)

        return analyzed

    def _generate_abnormality_summary(self) -> Dict[str, Any]:
        """
        Compute abnormality summary: counts, distribution, threat level.
        """
        total_frames = len(self.frame_classifications)
        abnormal_frames = len(self.abnormal_frames)

        ab_types: List[str] = []
        for fr in self.abnormal_frames:
            for ab in fr.get("abnormalities", []):
                ab_types.append(ab.get("type", "unknown"))

        distribution = Counter(ab_types)
        abnormal_pct = (abnormal_frames / total_frames * 100.0) if total_frames > 0 else 0.0

        threat_level = "LOW"
        if abnormal_pct > 30:
            threat_level = "CRITICAL"
        elif abnormal_pct > 15:
            threat_level = "HIGH"
        elif abnormal_pct > 5:
            threat_level = "MEDIUM"

        return {
            "total_frames_analyzed": total_frames,
            "abnormal_frames": abnormal_frames,
            "abnormal_percentage": round(abnormal_pct, 2),
            "threat_level": threat_level,
            "abnormality_types": dict(distribution),
            "total_threats_detected": int(self.total_threats),
        }

    def _print_complete_summary(self, summary: Dict[str, Any], video_info: Dict[str, Any]) -> None:
        print("\n" + "=" * 70)
        print("📊 COMPLETE ANALYTICS SUMMARY")
        print("=" * 70)
        print(f"🎥 Video: {video_info.get('filename')}")
        print(f"⏱️  Duration: {video_info.get('duration', 0):.2f}s")

        print("\n👥 VISITOR STATISTICS (Behavior)")
        print("-" * 70)
        print(f"Total Visitors: {summary.get('total_visitors', 0)}")
        print(f"Purchasers: {summary.get('purchasers', 0)}")
        print(f"Window Shoppers: {summary.get('window_shoppers', 0)}")
        print(f"Browsers: {summary.get('browsers', 0)}")
        print(f"Passing Through: {summary.get('passing_through', 0)}")
        print(f"Conversion Rate: {summary.get('conversion_rate', 0)}%")
        print(f"Avg Visit Duration: {summary.get('avg_visit_duration', 0):.2f}s")

        print("\n⚠️ THREAT ANALYSIS")
        print("-" * 70)
        print(f"Threat Level: {summary.get('threat_level', 'UNKNOWN')}")
        print(f"Abnormal Frames: {summary.get('abnormal_frames', 0)} ({summary.get('abnormal_percentage', 0)}%)")
        print(f"Total Threats: {summary.get('total_threats_detected', 0)}")

        if summary.get("abnormality_types"):
            print("\nThreat Types Detected:")
            for t, c in summary["abnormality_types"].items():
                print(f"  - {t}: {c}")

    def _export_complete_report(self, summary: Dict[str, Any], video_info: Dict[str, Any], base_path: Path) -> str:
        """
        Write a text report to disk.
        base_path can be output video path or a folder reference.
        """
        # If base_path ends with .mp4 etc, use its parent
        if base_path.suffix.lower() in [".mp4", ".avi", ".mov", ".mkv"]:
            report_path = base_path.parent / f"{base_path.stem}_complete_report.txt"
        else:
            report_path = base_path.parent / f"{video_info.get('filename','video')}_complete_report.txt"

        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("COMPLETE VIDEO ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Video: {video_info.get('filename')}\n")
            f.write(f"Duration: {video_info.get('duration', 0):.2f}s\n")
            f.write(f"Resolution: {video_info.get('width','?')}x{video_info.get('height','?')}\n\n")

            f.write("BEHAVIOR ANALYSIS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total Visitors: {summary.get('total_visitors', 0)}\n")
            f.write(f"Purchasers: {summary.get('purchasers', 0)}\n")
            f.write(f"Window Shoppers: {summary.get('window_shoppers', 0)}\n")
            f.write(f"Browsers: {summary.get('browsers', 0)}\n")
            f.write(f"Passing Through: {summary.get('passing_through', 0)}\n")
            f.write(f"Conversion Rate: {summary.get('conversion_rate', 0)}%\n")
            f.write(f"Avg Visit Duration: {summary.get('avg_visit_duration', 0):.2f}s\n\n")

            f.write("THREAT ANALYSIS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Threat Level: {summary.get('threat_level', 'UNKNOWN')}\n")
            f.write(f"Total Frames Analyzed: {summary.get('total_frames_analyzed', 0)}\n")
            f.write(f"Abnormal Frames: {summary.get('abnormal_frames', 0)} ({summary.get('abnormal_percentage', 0)}%)\n")
            f.write(f"Total Threats Detected: {summary.get('total_threats_detected', 0)}\n\n")

            if summary.get("abnormality_types"):
                f.write("THREAT TYPES\n")
                f.write("-" * 70 + "\n")
                for t, c in summary["abnormality_types"].items():
                    f.write(f"{t}: {c}\n")
                f.write("\n")

            f.write("ABNORMAL FRAMES TIMELINE (first 50)\n")
            f.write("-" * 70 + "\n")
            for fr in self.abnormal_frames[:50]:
                f.write(
                    f"Frame {fr['frame_num']} ({fr['timestamp']:.2f}s): {fr['abnormal_count']} threats\n"
                )
            if len(self.abnormal_frames) > 50:
                f.write(f"... and {len(self.abnormal_frames) - 50} more\n")

        print(f"📄 Complete report saved: {report_path}")
        return str(report_path)


# ============================================================
# ✅ Compatibility Export (THIS FIXES YOUR IMPORT ERROR)
# ============================================================

# Your GUI/test does: from core.video_processor import VideoProcessor
# This line guarantees it exists.
VideoProcessor = CompleteVideoProcessor

__all__ = ["VideoProcessor", "CompleteVideoProcessor"]


if __name__ == "__main__":
    print("✅ Complete Video Processor Ready")
    print("🎯 Features:")
    print("  - Person detection & tracking")
    print("  - Behavior analysis (shopping patterns)")
    print("  - Pose estimation with threat detection")
    print("  - Clothing classification")
    print("  - Object detection")
    print("  - Abnormality/threat detection")
    print("  - Red/Green box visualization")
    print("  - Complete analytics reports")
    print("  - CSV export")
