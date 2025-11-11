"""
Video Processing Engine for Eyeora AI-CCTV
Processes videos, tracks people, analyzes behavior, and generates reports
"""

import cv2
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from ultralytics import YOLO

from config import (
    MODEL_PATH, CONFIDENCE_THRESHOLD, IOU_THRESHOLD,
    VIDEO_FPS_PROCESS, VIDEO_OUTPUT_FPS, PROCESSED_DIR,
    YOLO_MODEL, MODELS_DIR
)
from tracker import PersonTracker, Detection, Track
from behavior_analyzer import BehaviorAnalyzer, draw_zones
from csv_exporter import DataExporter


class VideoProcessor:
    """
    Main video processing engine
    Handles video input, detection, tracking, and analysis
    """
    
    def __init__(self, model_path: str = None, show_zones: bool = True):
        """
        Initialize video processor
        
        Args:
            model_path: Path to YOLO model
            show_zones: Whether to draw zones on output video
        """
        self.model_path = model_path or MODEL_PATH
        self.show_zones = show_zones
        
        # Initialize components
        print("🚀 Initializing Video Processor...")
        self.model = self._load_model()
        self.tracker = None  # Initialized per video
        self.analyzer = None  # Initialized per video
        self.exporter = DataExporter()
        
        print("✅ Video Processor Ready")
    
    def _load_model(self) -> YOLO:
        """Load YOLO model"""
        print(f"📦 Loading YOLO model: {self.model_path}")
        
        # Check if model exists
        if not Path(self.model_path).exists():
            print(f"⚠️  Model not found at {self.model_path}")
            print(f"📥 Downloading {YOLO_MODEL}...")
            model = YOLO(YOLO_MODEL)
            # Save to models directory
            MODELS_DIR.mkdir(exist_ok=True)
            print(f"✅ Model saved to {MODELS_DIR}")
        else:
            model = YOLO(str(self.model_path))
        
        print(f"✅ Model loaded: {self.model_path}")
        return model
    
    def process_video(
        self,
        video_path: str,
        output_path: str = None,
        generate_output_video: bool = True,
        export_csv: bool = True
    ) -> Dict:
        """
        Process a video file - main entry point
        
        Args:
            video_path: Path to input video
            output_path: Path for output video (auto-generated if None)
            generate_output_video: Whether to create annotated output video
            export_csv: Whether to export analytics to CSV
            
        Returns:
            Dictionary with processing results and paths
        """
        print("\n" + "="*60)
        print("🎥 VIDEO PROCESSING STARTED")
        print("="*60)
        
        start_time = time.time()
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        video_info = {
            "filename": video_path.name,
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": duration
        }
        
        print(f"📹 Video: {video_path.name}")
        print(f"📊 Resolution: {width}x{height}")
        print(f"⏱️  Duration: {duration:.2f}s ({frame_count} frames @ {fps:.2f} fps)")
        
        # Initialize tracker and analyzer
        self.tracker = PersonTracker(
            max_age=30,
            min_hits=3,
            iou_threshold=0.3
        )
        self.analyzer = BehaviorAnalyzer(width, height, fps)
        
        # Setup output video writer
        output_writer = None
        if generate_output_video:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = PROCESSED_DIR / "videos" / f"processed_{timestamp}.mp4"
            else:
                output_path = Path(output_path)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            output_writer = cv2.VideoWriter(
                str(output_path),
                fourcc,
                VIDEO_OUTPUT_FPS,
                (width, height)
            )
            print(f"🎬 Output video: {output_path}")
        
        # Process frames
        frame_num = 0
        processed_frames = 0
        
        print("\n🔄 Processing frames...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_num += 1
            timestamp = frame_num / fps
            
            # Process every Nth frame for efficiency
            if frame_num % VIDEO_FPS_PROCESS == 0:
                processed_frames += 1
                
                # Detect people in frame
                detections = self._detect_people(frame)
                
                # Update tracker
                active_tracks = self.tracker.update(detections, timestamp)
                
                # Annotate frame
                if generate_output_video:
                    annotated_frame = self._annotate_frame(
                        frame.copy(),
                        active_tracks,
                        timestamp
                    )
                    output_writer.write(annotated_frame)
                
                # Progress update
                if processed_frames % 50 == 0:
                    progress = (frame_num / frame_count) * 100
                    print(f"⏳ Progress: {progress:.1f}% | Active tracks: {len(active_tracks)}")
        
        # Cleanup
        cap.release()
        if output_writer:
            output_writer.release()
        
        print("\n✅ Frame processing completed")
        
        # Analyze all tracks
        print("\n📊 Analyzing customer behaviors...")
        all_tracks = self.tracker.get_completed_tracks()
        analyzed_tracks = []
        
        for track in all_tracks:
            analysis = self.analyzer.analyze_track(track)
            analyzed_tracks.append(analysis)
        
        print(f"✅ Analyzed {len(analyzed_tracks)} customer journeys")
        
        # Generate summary
        summary = self.analyzer.generate_summary(analyzed_tracks)
        
        # Print summary
        self._print_summary(summary, video_info)
        
        # Export data
        csv_path = None
        if export_csv and analyzed_tracks:
            print("\n💾 Exporting analytics data...")
            csv_path = self.exporter.export_to_csv(
                analyzed_tracks,
                include_summary=True
            )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        print("\n" + "="*60)
        print(f"✅ PROCESSING COMPLETED in {processing_time:.2f}s")
        print("="*60)
        
        return {
            "success": True,
            "video_info": video_info,
            "output_video_path": str(output_path) if generate_output_video else None,
            "csv_path": csv_path,
            "total_tracks": len(analyzed_tracks),
            "summary": summary,
            "processing_time": processing_time,
            "analyzed_tracks": analyzed_tracks
        }
    
    def _detect_people(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect people in a frame using YOLO
        
        Args:
            frame: Video frame
            
        Returns:
            List of Detection objects
        """
        # Run YOLO detection
        results = self.model(
            frame,
            conf=CONFIDENCE_THRESHOLD,
            iou=IOU_THRESHOLD,
            classes=[0],  # Only detect 'person' class
            verbose=False
        )[0]
        
        detections = []
        
        # Convert YOLO results to Detection objects
        for box in results.boxes:
            bbox = box.xyxy[0].cpu().numpy().tolist()  # [x1, y1, x2, y2]
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            
            detection = Detection(
                bbox=bbox,
                confidence=confidence,
                class_id=class_id,
                class_name="person"
            )
            detections.append(detection)
        
        return detections
    
    def _annotate_frame(
        self,
        frame: np.ndarray,
        tracks: List[Track],
        timestamp: float
    ) -> np.ndarray:
        """
        Annotate frame with tracking information
        
        Args:
            frame: Video frame
            tracks: Active tracks
            timestamp: Current timestamp
            
        Returns:
            Annotated frame
        """
        # Draw zones if enabled
        if self.show_zones:
            frame = draw_zones(frame, self.analyzer.zone_detector)
        
        # Draw each track
        for track in tracks:
            if not track.positions:
                continue
            
            # Get last position
            last_pos = track.last_position
            if last_pos is None:
                continue
            
            x, y = last_pos
            x, y = int(x), int(y)
            
            # Get bounding box if available
            if track.detections:
                bbox = track.detections[-1].bbox
                x1, y1, x2, y2 = map(int, bbox)
                
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw track ID
                label = f"ID: {track.track_id}"
                cv2.putText(
                    frame, label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 255, 0), 2
                )
            
            # Draw trajectory (last 30 positions)
            if len(track.positions) > 1:
                points = track.positions[-30:]
                points = [(int(p[0]), int(p[1])) for p in points]
                
                for i in range(1, len(points)):
                    cv2.line(frame, points[i-1], points[i], (255, 0, 0), 2)
        
        # Draw info overlay
        info_text = [
            f"Active Tracks: {len(tracks)}",
            f"Time: {timestamp:.1f}s"
        ]
        
        y_offset = 30
        for text in info_text:
            cv2.putText(
                frame, text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (255, 255, 255), 2
            )
            y_offset += 30
        
        return frame
    
    def _print_summary(self, summary: Dict, video_info: Dict):
        """Print analytics summary"""
        print("\n" + "="*60)
        print("📊 ANALYTICS SUMMARY")
        print("="*60)
        
        print(f"\n🎥 Video: {video_info['filename']}")
        print(f"⏱️  Duration: {video_info['duration']:.2f}s")
        
        print(f"\n👥 VISITOR STATISTICS")
        print("-"*60)
        print(f"Total Visitors: {summary['total_visitors']}")
        print(f"Total Customers (Purchased): {summary['purchasers']}")
        print(f"Window Shoppers: {summary['window_shoppers']}")
        print(f"Browsers: {summary['browsers']}")
        print(f"Passing Through: {summary['passing_through']}")
        print(f"Idle: {summary['idle']}")
        
        print(f"\n💰 KEY METRICS")
        print("-"*60)
        print(f"Conversion Rate: {summary['conversion_rate']}%")
        print(f"Average Visit Duration: {summary['avg_visit_duration']:.2f}s")
        print(f"Checkout Area Visitors: {summary['total_checkout_visitors']}")
    
    def process_image(self, image_path: str, output_path: str = None) -> Dict:
        """
        Process a single image (for testing/demo)
        
        Args:
            image_path: Path to input image
            output_path: Path for output image
            
        Returns:
            Detection results
        """
        print(f"\n📸 Processing image: {image_path}")
        
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Read image
        frame = cv2.imread(str(image_path))
        height, width = frame.shape[:2]
        
        # Detect people
        detections = self._detect_people(frame)
        
        print(f"✅ Detected {len(detections)} people")
        
        # Annotate image
        for detection in detections:
            x1, y1, x2, y2 = map(int, detection.bbox)
            conf = detection.confidence
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"Person {conf:.2f}"
            cv2.putText(
                frame, label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 255, 0), 2
            )
        
        # Save output
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = PROCESSED_DIR / "images" / f"detected_{timestamp}.jpg"
        else:
            output_path = Path(output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), frame)
        
        print(f"💾 Saved to: {output_path}")
        
        return {
            "success": True,
            "detections": len(detections),
            "output_path": str(output_path),
            "image_info": {
                "width": width,
                "height": height
            }
        }


if __name__ == "__main__":
    print("🎬 Video Processor Module Ready")
    print("📹 Capabilities: Video/Image processing, People tracking, Behavior analysis")
    print("\n💡 Usage:")
    print("  processor = VideoProcessor()")
    print("  result = processor.process_video('input.mp4')")