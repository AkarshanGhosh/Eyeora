"""
Detection Engine - YOLO Model Wrapper
Handles object detection with automatic model management
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


class DetectionEngine:
    def __init__(
        self,
        model_name: str = None,
        confidence_threshold: float = None,
        iou_threshold: float = None,
        device: str = None
    ):
        self.model_name = model_name or YOLO_MODEL
        self.confidence_threshold = confidence_threshold or CONFIDENCE_THRESHOLD
        self.iou_threshold = iou_threshold or IOU_THRESHOLD

        # ✅ Safe device selection
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            if device == 'cuda' and not torch.cuda.is_available():
                print("⚠️ CUDA requested but not available in this PyTorch build. Falling back to CPU.")
                self.device = 'cpu'
            else:
                self.device = device

        print("🚀 Initializing Detection Engine...")
        print(f"📱 Device: {self.device.upper()}")

        self.model = self._load_model()
        self.model_loaded = True
        print("✅ Detection Engine Ready")
    """
    YOLO-based detection engine with automatic model management
    Supports multiple detection modes and custom configurations
    """
    
    # COCO dataset class names (80 classes)
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
        device: str = None
    ):
        """
        Initialize Detection Engine
        
        Args:
            model_name: YOLO model name (e.g., 'yolo11x.pt')
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: Device to run on ('cuda', 'cpu', or None for auto)
        """
        self.model_name = model_name or YOLO_MODEL
        self.confidence_threshold = confidence_threshold or CONFIDENCE_THRESHOLD
        self.iou_threshold = iou_threshold or IOU_THRESHOLD
        
        # Auto-detect device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        print(f"🚀 Initializing Detection Engine...")
        print(f"📱 Device: {self.device.upper()}")
        
        # Load model
        self.model = self._load_model()
        self.model_loaded = True
        
        print(f"✅ Detection Engine Ready")
    
    def _load_model(self) -> YOLO:
        """Load or download YOLO model"""
        model_path = MODELS_DIR / self.model_name
        
        # Create models directory if it doesn't exist
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Check if model exists locally
        if model_path.exists():
            print(f"📦 Loading model from: {model_path}")
            model = YOLO(str(model_path))
        else:
            print(f"📥 Model not found. Downloading {self.model_name}...")
            model = YOLO(self.model_name)  # This will download automatically
            print(f"✅ Model downloaded and cached")
        
        # Move model to device
        model.to(self.device)
        
        return model
    
    def detect_people(
        self,
        image: np.ndarray,
        confidence: float = None,
        return_crops: bool = False
    ) -> Tuple[List[Detection], Optional[List[np.ndarray]]]:
        """
        Detect only people in an image
        
        Args:
            image: Input image (BGR format)
            confidence: Override confidence threshold
            return_crops: Whether to return cropped person images
            
        Returns:
            Tuple of (detections list, crops list if requested)
        """
        conf = confidence or self.confidence_threshold
        
        # Run detection only for 'person' class (class 0)
        results = self.model(
            image,
            conf=conf,
            iou=self.iou_threshold,
            classes=[0],  # Only person
            verbose=False,
            device=self.device
        )[0]
        
        detections = []
        crops = [] if return_crops else None
        
        for box in results.boxes:
            bbox = box.xyxy[0].cpu().numpy().tolist()  # [x1, y1, x2, y2]
            confidence_score = float(box.conf[0])
            class_id = int(box.cls[0])
            
            detection = Detection(
                bbox=bbox,
                confidence=confidence_score,
                class_id=class_id,
                class_name="person"
            )
            detections.append(detection)
            
            # Extract crop if requested
            if return_crops:
                x1, y1, x2, y2 = map(int, bbox)
                crop = image[y1:y2, x1:x2].copy()
                crops.append(crop)
        
        return detections, crops
    
    def detect_all_objects(
        self,
        image: np.ndarray,
        confidence: float = None,
        classes: List[int] = None
    ) -> List[Detection]:
        """
        Detect all objects or specific classes
        
        Args:
            image: Input image
            confidence: Override confidence threshold
            classes: List of class IDs to detect (None for all)
            
        Returns:
            List of Detection objects
        """
        conf = confidence or self.confidence_threshold
        
        results = self.model(
            image,
            conf=conf,
            iou=self.iou_threshold,
            classes=classes,
            verbose=False,
            device=self.device
        )[0]
        
        detections = []
        
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
            detections.append(detection)
        
        return detections
    
    def detect_batch(
        self,
        images: List[np.ndarray],
        confidence: float = None,
        person_only: bool = True
    ) -> List[List[Detection]]:
        """
        Batch detection for multiple images (more efficient)
        
        Args:
            images: List of images
            confidence: Override confidence threshold
            person_only: Only detect people
            
        Returns:
            List of detection lists (one per image)
        """
        conf = confidence or self.confidence_threshold
        classes = [0] if person_only else None
        
        # Run batch inference
        results = self.model(
            images,
            conf=conf,
            iou=self.iou_threshold,
            classes=classes,
            verbose=False,
            device=self.device
        )
        
        all_detections = []
        
        for result in results:
            detections = []
            for box in result.boxes:
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
                detections.append(detection)
            
            all_detections.append(detections)
        
        return all_detections
    
    def count_people(self, image: np.ndarray, confidence: float = None) -> int:
        """
        Quick people counting without full detection data
        
        Args:
            image: Input image
            confidence: Override confidence threshold
            
        Returns:
            Number of people detected
        """
        detections, _ = self.detect_people(image, confidence)
        return len(detections)
    
    def detect_security_objects(
        self,
        image: np.ndarray,
        confidence: float = None
    ) -> Dict[str, List[Detection]]:
        """
        Detect security-relevant objects (bags, person, etc.)
        
        Args:
            image: Input image
            confidence: Override confidence threshold
            
        Returns:
            Dictionary with categorized detections
        """
        # Security relevant classes
        security_classes = {
            'person': 0,
            'backpack': 24,
            'handbag': 26,
            'suitcase': 28
        }
        
        class_ids = list(security_classes.values())
        
        all_detections = self.detect_all_objects(image, confidence, class_ids)
        
        # Categorize detections
        categorized = {name: [] for name in security_classes.keys()}
        
        for detection in all_detections:
            for name, class_id in security_classes.items():
                if detection.class_id == class_id:
                    categorized[name].append(detection)
                    break
        
        return categorized
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "num_classes": len(self.COCO_CLASSES),
            "model_loaded": self.model_loaded,
            "cuda_available": torch.cuda.is_available()
        }
    
    def change_threshold(self, confidence: float = None, iou: float = None):
        """
        Update detection thresholds
        
        Args:
            confidence: New confidence threshold
            iou: New IoU threshold
        """
        if confidence is not None:
            self.confidence_threshold = confidence
            print(f"✅ Confidence threshold updated: {confidence}")
        
        if iou is not None:
            self.iou_threshold = iou
            print(f"✅ IoU threshold updated: {iou}")
    
    def visualize_detections(
        self,
        image: np.ndarray,
        detections: List[Detection],
        show_confidence: bool = True,
        thickness: int = 2
    ) -> np.ndarray:
        """
        Draw bounding boxes on image
        
        Args:
            image: Input image
            detections: List of detections to draw
            show_confidence: Show confidence scores
            thickness: Line thickness
            
        Returns:
            Annotated image
        """
        annotated = image.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = map(int, detection.bbox)
            
            # Color based on class (green for person)
            color = (0, 255, 0) if detection.class_name == "person" else (255, 0, 0)
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
            
            # Draw label
            label = detection.class_name
            if show_confidence:
                label += f" {detection.confidence:.2f}"
            
            # Background for text
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - h - 4), (x1 + w, y1), color, -1)
            cv2.putText(
                annotated, label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1
            )
        
        return annotated


class ModelManager:
    """
    Manages multiple YOLO models
    Useful for having different models for different purposes
    """
    
    AVAILABLE_MODELS = {
        'nano': 'yolo11n.pt',      # Fastest, least accurate
        'small': 'yolo11s.pt',     # Fast, good accuracy
        'medium': 'yolo11m.pt',    # Balanced
        'large': 'yolo11l.pt',     # Slow, high accuracy
        'xlarge': 'yolo11x.pt'     # Slowest, best accuracy
    }
    
    def __init__(self):
        self.engines = {}
        self.active_engine = None
    
    def load_model(self, model_type: str = 'xlarge') -> DetectionEngine:
        """
        Load a specific model
        
        Args:
            model_type: Model type ('nano', 'small', 'medium', 'large', 'xlarge')
            
        Returns:
            DetectionEngine instance
        """
        if model_type not in self.AVAILABLE_MODELS:
            raise ValueError(f"Unknown model type: {model_type}. Available: {list(self.AVAILABLE_MODELS.keys())}")
        
        model_name = self.AVAILABLE_MODELS[model_type]
        
        # Check if already loaded
        if model_type in self.engines:
            print(f"♻️  Reusing cached {model_type} model")
            self.active_engine = self.engines[model_type]
            return self.active_engine
        
        # Load new model
        print(f"🔄 Loading {model_type} model: {model_name}")
        engine = DetectionEngine(model_name=model_name)
        
        self.engines[model_type] = engine
        self.active_engine = engine
        
        return engine
    
    def get_active_engine(self) -> Optional[DetectionEngine]:
        """Get currently active engine"""
        return self.active_engine
    
    def list_loaded_models(self) -> List[str]:
        """List all loaded models"""
        return list(self.engines.keys())
    
    def clear_cache(self):
        """Clear all loaded models from memory"""
        self.engines.clear()
        self.active_engine = None
        print("🧹 Model cache cleared")


if __name__ == "__main__":
    print("✅ Detection Engine Module Ready")
    print("🎯 Capabilities:")
    print("  - Person detection")
    print("  - Multi-object detection")
    print("  - Batch processing")
    print("  - Security object detection")
    print("  - Automatic model management")
    print("\n💡 Usage:")
    print("  engine = DetectionEngine()")
    print("  detections, _ = engine.detect_people(image)")