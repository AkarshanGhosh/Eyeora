"""
Enhanced Detection Engine with Abnormality Detection
Detects weapons, suspicious objects, and abnormal behaviors
Location: Software Code/Server/core/detection_engine.py
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from ultralytics import YOLO
import torch

from core.config import (
    MODEL_PATH, MODELS_DIR, CONFIDENCE_THRESHOLD, 
    IOU_THRESHOLD, MAX_DETECTIONS, YOLO_MODEL
)
from core.tracker import Detection


class AbnormalityDetector:
    """Detects abnormal objects and behaviors"""
    
    THREAT_OBJECTS = {
        'knife': 43,
        'scissors': 76,
    }
    
    SUSPICIOUS_BEHAVIORS = [
        'pointing',
        'aiming',
        'threatening_gesture'
    ]
    
    def __init__(self):
        """Initialize abnormality detector"""
        self.threat_history = {}
        self.alert_threshold = 0.6
        self.weapon_model = self._load_weapon_model()
    
    def _load_weapon_model(self) -> Optional[YOLO]:
        """Load specialized weapon detection model if available"""
        weapon_model_path = MODELS_DIR / "weapon_detection.pt"
        
        if weapon_model_path.exists():
            print("🔫 Loading weapon detection model...")
            return YOLO(str(weapon_model_path))
        else:
            print("⚠️ No specialized weapon model found. Using COCO model only.")
            return None
    
    def detect_weapons(self, image: np.ndarray) -> List[Detection]:
        """Detect weapons in image using specialized model"""
        if self.weapon_model is None:
            return []
        
        try:
            results = self.weapon_model(image, conf=self.alert_threshold, verbose=False)[0]
            
            detections = []
            for box in results.boxes:
                bbox = box.xyxy[0].cpu().numpy().tolist()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = results.names[class_id] if class_id in results.names else "weapon"
                
                detection = Detection(
                    bbox=bbox,
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name
                )
                detections.append(detection)
            
            return detections
            
        except Exception as e:
            print(f"❌ Weapon detection error: {e}")
            return []
    
    def classify_abnormality(self, detection: Detection) -> Dict:
        """Classify if detection is abnormal - ONLY for actual weapons"""
        threat_objects = ['knife', 'scissors', 'gun', 'weapon', 'handgun', 'pistol', 'rifle']
        
        is_abnormal = False
        abnormality_type = "normal"
        confidence = detection.confidence
        
        if any(threat in detection.class_name.lower() for threat in threat_objects):
            is_abnormal = True
            abnormality_type = "weapon_detected"
        
        return {
            "is_abnormal": is_abnormal,
            "type": abnormality_type,
            "confidence": confidence,
            "requires_alert": is_abnormal and confidence > self.alert_threshold
        }


def apply_nms_to_detections(detections: List[Detection], iou_threshold: float = 0.4) -> List[Detection]:
    """Apply Non-Maximum Suppression to remove duplicate detections"""
    if len(detections) == 0:
        return []
    
    boxes = np.array([d.bbox for d in detections])
    scores = np.array([d.confidence for d in detections])
    
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        
        iou = inter / (areas[i] + areas[order[1:]] - inter)
        
        inds = np.where(iou <= iou_threshold)[0]
        order = order[inds + 1]
    
    return [detections[i] for i in keep]


class EnhancedDetectionEngine:
    """Enhanced detection engine with abnormality detection"""
    
    COCO_CLASSES = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
        'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
        'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
        'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
        'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
        'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
        'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
        'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
        'toothbrush'
    ]
    
    def __init__(
        self,
        model_name: str = None,
        confidence_threshold: float = None,
        iou_threshold: float = None,
        device: str = None,
        enable_abnormality: bool = True
    ):
        """Initialize enhanced detection engine"""
        self.model_name = model_name or YOLO_MODEL
        self.confidence_threshold = confidence_threshold or CONFIDENCE_THRESHOLD
        self.iou_threshold = iou_threshold or IOU_THRESHOLD
        
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            if device == 'cuda' and not torch.cuda.is_available():
                print("⚠️ CUDA requested but not available. Falling back to CPU.")
                self.device = 'cpu'
            else:
                self.device = device
        
        print(f"🚀 Initializing Enhanced Detection Engine...")
        print(f"📱 Device: {self.device.upper()}")
        
        self.model = self._load_model()
        self.model_loaded = True
        
        try:
            self.pose_model = YOLO('yolo11n-pose.pt')
            self.pose_enabled = True
            print("✅ Pose detection enabled")
        except:
            self.pose_model = None
            self.pose_enabled = False
            print("⚠️ Pose detection not available")
        
        self.abnormality_detector = AbnormalityDetector() if enable_abnormality else None
        
        print(f"✅ Enhanced Detection Engine Ready")
    
    def _load_model(self) -> YOLO:
        """Load YOLO model"""
        model_path = MODELS_DIR / self.model_name
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        
        if model_path.exists():
            print(f"📦 Loading model from: {model_path}")
            model = YOLO(str(model_path))
        else:
            print(f"📥 Downloading {self.model_name}...")
            model = YOLO(self.model_name)
            print(f"✅ Model downloaded")
        
        model.to(self.device)
        return model
    
    def detect_with_abnormality(
        self,
        image: np.ndarray,
        confidence: float = None,
        detect_poses: bool = True
    ) -> Tuple[List[Dict], List[Dict]]:
        """Detect objects with abnormality classification - weapons only marked as abnormal"""
        conf = confidence or self.confidence_threshold
        
        results = self.model(
            image,
            conf=conf,
            iou=self.iou_threshold,
            verbose=False,
            device=self.device,
            max_det=100
        )[0]
        
        all_detections = []
        for box in results.boxes:
            bbox = box.xyxy[0].cpu().numpy().tolist()
            confidence_score = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self.COCO_CLASSES[class_id] if class_id < len(self.COCO_CLASSES) else "unknown"
            
            detection = Detection(
                bbox=bbox,
                confidence=confidence_score,
                class_id=class_id,
                class_name=class_name
            )
            all_detections.append(detection)
        
        all_detections = apply_nms_to_detections(all_detections, iou_threshold=0.45)
        
        weapon_detections = []
        if self.abnormality_detector:
            weapon_detections = self.abnormality_detector.detect_weapons(image)
            weapon_detections = apply_nms_to_detections(weapon_detections, iou_threshold=0.45)
        
        normal_detections = []
        abnormal_detections = []
        
        for detection in all_detections:
            if self.abnormality_detector:
                abnormality = self.abnormality_detector.classify_abnormality(detection)
            else:
                abnormality = {"is_abnormal": False, "type": "normal", "confidence": detection.confidence}
            
            detection_dict = {
                "detection": detection,
                "abnormality": abnormality,
                "bbox": detection.bbox,
                "confidence": detection.confidence,
                "class_name": detection.class_name
            }
            
            if abnormality["is_abnormal"]:
                abnormal_detections.append(detection_dict)
            else:
                normal_detections.append(detection_dict)
        
        for weapon in weapon_detections:
            abnormal_detections.append({
                "detection": weapon,
                "abnormality": {
                    "is_abnormal": True,
                    "type": "weapon_detected",
                    "confidence": weapon.confidence,
                    "requires_alert": True
                },
                "bbox": weapon.bbox,
                "confidence": weapon.confidence,
                "class_name": weapon.class_name
            })
        
        return normal_detections, abnormal_detections
    
    def detect_all_objects(self, image: np.ndarray, classes: Optional[List[int]] = None) -> List[Detection]:
        """Detect all objects without abnormality classification"""
        results = self.model(
            image,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False,
            device=self.device,
            classes=classes,
            max_det=100
        )[0]
        
        detections = []
        for box in results.boxes:
            bbox = box.xyxy[0].cpu().numpy().tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self.COCO_CLASSES[class_id] if class_id < len(self.COCO_CLASSES) else "unknown"
            
            detection = Detection(
                bbox=bbox,
                confidence=confidence,
                class_id=class_id,
                class_name=class_name
            )
            detections.append(detection)
        
        detections = apply_nms_to_detections(detections, iou_threshold=0.45)
        
        return detections
    
    def visualize_with_abnormality(
        self,
        image: np.ndarray,
        normal_detections: List[Dict],
        abnormal_detections: List[Dict],
        show_confidence: bool = True,
        thickness: int = 2
    ) -> np.ndarray:
        """Visualize detections with green (normal) and red (abnormal/weapon) boxes"""
        annotated = image.copy()
        
        for det_dict in normal_detections:
            x1, y1, x2, y2 = map(int, det_dict["bbox"])
            color = (0, 255, 0)
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
            
            label = det_dict['class_name']
            if show_confidence:
                label += f" {det_dict['confidence']:.2f}"
            
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - h - 4), (x1 + w, y1), color, -1)
            cv2.putText(annotated, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        for det_dict in abnormal_detections:
            x1, y1, x2, y2 = map(int, det_dict["bbox"])
            color = (0, 0, 255)
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness + 1)
            
            abnormality_type = det_dict["abnormality"]["type"]
            label = f"⚠ {abnormality_type}"
            if show_confidence:
                label += f" {det_dict['confidence']:.2f}"
            
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated, (x1, y1 - h - 6), (x1 + w, y1), color, -1)
            cv2.putText(annotated, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.putText(annotated, "⚠", (x2 - 30, y1 + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        total_normal = len(normal_detections)
        total_abnormal = len(abnormal_detections)
        
        summary = f"Normal: {total_normal} | THREATS: {total_abnormal}"
        cv2.putText(annotated, summary, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        if total_abnormal > 0:
            cv2.putText(annotated, "⚠ WEAPON DETECTED ⚠", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        
        return annotated
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "pose_enabled": self.pose_enabled,
            "abnormality_detection": self.abnormality_detector is not None,
            "cuda_available": torch.cuda.is_available()
        }


if __name__ == "__main__":
    print("✅ Enhanced Detection Engine with Abnormality Detection Ready")
    print("🎯 Features:")
    print("  - Weapon-only threat detection")
    print("  - NMS ghost box removal")
    print("  - Color-coded visualization (Green=Normal, Red=Weapon)")
    
DetectionEngine = EnhancedDetectionEngine