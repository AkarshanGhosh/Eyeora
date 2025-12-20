"""
Enhanced Detection Engine with Clean Visualization
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
    
    def __init__(self):
        self.threat_history = {}
        self.alert_threshold = 0.6
        self.weapon_model = self._load_weapon_model()
    
    def _load_weapon_model(self) -> Optional[YOLO]:
        weapon_model_path = MODELS_DIR / "weapon_detection.pt"
        
        if weapon_model_path.exists():
            print("🔫 Loading weapon detection model...")
            return YOLO(str(weapon_model_path))
        else:
            print("⚠️ No specialized weapon model found.")
            return None
    
    def detect_weapons(self, image: np.ndarray) -> List[Detection]:
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
            return []
    
    def classify_abnormality(self, detection: Detection) -> Dict:
        threat_objects = ['knife', 'scissors', 'gun', 'weapon', 'handgun', 'pistol', 'rifle']
        
        is_abnormal = any(threat in detection.class_name.lower() for threat in threat_objects)
        
        return {
            "is_abnormal": is_abnormal,
            "type": "weapon_detected" if is_abnormal else "normal",
            "confidence": detection.confidence,
            "requires_alert": is_abnormal and detection.confidence > self.alert_threshold
        }


def apply_nms_to_detections(detections: List[Detection], iou_threshold: float = 0.5) -> List[Detection]:
    """Apply Non-Maximum Suppression"""
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
    """Enhanced detection engine with clean visualization"""
    
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
        conf = confidence or self.confidence_threshold
        
        results = self.model(
            image,
            conf=conf,
            iou=self.iou_threshold,
            verbose=False,
            device=self.device,
            max_det=50
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
        
        all_detections = apply_nms_to_detections(all_detections, iou_threshold=0.5)
        
        weapon_detections = []
        if self.abnormality_detector:
            weapon_detections = self.abnormality_detector.detect_weapons(image)
            weapon_detections = apply_nms_to_detections(weapon_detections, iou_threshold=0.5)
        
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
        results = self.model(
            image,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False,
            device=self.device,
            classes=classes,
            max_det=50
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
        
        detections = apply_nms_to_detections(detections, iou_threshold=0.5)
        
        return detections
    
    def visualize_with_abnormality(
        self,
        image: np.ndarray,
        normal_detections: List[Dict],
        abnormal_detections: List[Dict],
        show_confidence: bool = False,
        thickness: int = 1
    ) -> np.ndarray:
        """Clean visualization like Image 1"""
        annotated = image.copy()
        
        for det_dict in normal_detections:
            x1, y1, x2, y2 = map(int, det_dict["bbox"])
            color = (0, 255, 0)
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
            
            label = f"ID: {det_dict['class_name']}"
            
            cv2.putText(annotated, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        for det_dict in abnormal_detections:
            x1, y1, x2, y2 = map(int, det_dict["bbox"])
            color = (0, 0, 255)
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            label = f"⚠ WEAPON"
            
            cv2.putText(annotated, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        total_normal = len(normal_detections)
        total_abnormal = len(abnormal_detections)
        
        cv2.putText(annotated, f"Tracks: {total_normal}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.putText(annotated, f"Weapons: {total_abnormal}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated
    
    def get_model_info(self) -> Dict:
        return {
            "model_name": self.model_name,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "pose_enabled": self.pose_enabled,
            "abnormality_detection": self.abnormality_detector is not None,
            "cuda_available": torch.cuda.is_available()
        }


if __name__ == "__main__":
    print("✅ Enhanced Detection Engine Ready")
    
DetectionEngine = EnhancedDetectionEngine