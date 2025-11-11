"""
Detection API Routes
Organized endpoints for image and video detection
Location: Software Code/Server/routes/detect_routes.py
"""

from fastapi import APIRouter, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
from pathlib import Path
from datetime import datetime
import cv2

from core.config import UPLOADS_DIR, PROCESSED_DIR
from core.detection_engine import DetectionEngine
from core.video_processor import VideoProcessor
from utils.validators import validate_video_file, validate_image_file, sanitize_filename
from utils.video_utils import get_video_info, validate_video

router = APIRouter(prefix="/detect", tags=["Detection"])

# Global instances (will be initialized by main server)
detection_engine: Optional[DetectionEngine] = None
video_processor: Optional[VideoProcessor] = None

def init_detection_routes(engine: DetectionEngine, processor: VideoProcessor):
    """Initialize detection routes with engine and processor instances"""
    global detection_engine, video_processor
    detection_engine = engine
    video_processor = processor

# ----------------------------
# Image Detection
# ----------------------------
@router.post("/image")
async def detect_image(
    file: UploadFile = File(...),
    confidence: Optional[float] = Query(None, ge=0, le=1, description="Detection confidence threshold (0-1)"),
    return_analytics: bool = Query(False, description="Include detailed detection analytics"),
    visualize: bool = Query(True, description="Generate annotated image")
):
    """
    Detect people in an uploaded image
    
    **Parameters:**
    - **file**: Image file (JPG, PNG, BMP, WEBP)
    - **confidence**: Detection threshold (default: 0.4)
    - **return_analytics**: Include bbox, confidence, etc.
    - **visualize**: Create annotated output image
    
    **Returns:**
    - people_count: Number of people detected
    - annotated_file: Path to annotated image (if visualize=True)
    - detections: Detailed detection data (if return_analytics=True)
    """
    try:
        if detection_engine is None:
            return JSONResponse(
                {"error": "Detection engine not initialized"},
                status_code=500
            )
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = sanitize_filename(file.filename)
        filename = f"{timestamp}_{safe_filename}"
        
        # Save uploaded file
        uploaded_path = UPLOADS_DIR / "images" / filename
        uploaded_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(uploaded_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"📥 Image uploaded: {filename}")
        
        # Validate image
        is_valid, message = validate_image_file(str(uploaded_path))
        if not is_valid:
            return JSONResponse({"error": message}, status_code=400)
        
        # Read image
        image = cv2.imread(str(uploaded_path))
        if image is None:
            return JSONResponse({"error": "Failed to read image"}, status_code=400)
        
        # Detect people
        detections, crops = detection_engine.detect_people(
            image,
            confidence=confidence,
            return_crops=return_analytics
        )
        
        print(f"✅ Detected {len(detections)} people")
        
        response = {
            "status": "success",
            "people_count": len(detections),
            "original_file": f"/uploads/images/{filename}",
            "timestamp": timestamp,
            "image_info": {
                "width": image.shape[1],
                "height": image.shape[0]
            }
        }
        
        # Generate annotated image if requested
        if visualize and len(detections) > 0:
            annotated = detection_engine.visualize_detections(image, detections)
            processed_path = PROCESSED_DIR / "images" / filename
            processed_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(processed_path), annotated)
            response["annotated_file"] = f"/processed/images/{filename}"
        
        # Include detailed analytics if requested
        if return_analytics:
            response["detections"] = [
                {
                    "bbox": det.bbox,
                    "confidence": round(det.confidence, 3),
                    "center": det.center,
                    "area": round(det.area, 2)
                }
                for det in detections
            ]
        
        return response
        
    except Exception as e:
        print(f"❌ Image detection error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


# ----------------------------
# Video Detection with Full Analytics
# ----------------------------
@router.post("/video")
async def detect_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    generate_output: bool = Query(True, description="Generate annotated output video"),
    export_csv: bool = Query(True, description="Export analytics to CSV"),
    confidence: Optional[float] = Query(None, ge=0, le=1, description="Detection confidence threshold")
):
    """
    Process video with full people tracking and behavior analysis
    
    **Parameters:**
    - **file**: Video file (MP4, AVI, MOV, MKV, etc.)
    - **generate_output**: Create annotated output video with tracking
    - **export_csv**: Export detailed analytics to CSV
    - **confidence**: Detection threshold (default: 0.4)
    
    **Returns:**
    - video_info: Resolution, FPS, duration, etc.
    - analytics: Visitor counts, behaviors, conversion rate
    - files: Links to annotated video and CSV report
    - processing_time: Time taken to process
    
    **Behavior Types Detected:**
    - Window Shopping: Quick look, minimal browsing
    - Browsing: Looking around, spending time
    - Purchasing: Visited checkout area
    - Idle: Standing still for extended time
    - Passing Through: Just walking through
    """
    try:
        if video_processor is None:
            return JSONResponse(
                {"error": "Video processor not initialized"},
                status_code=500
            )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = sanitize_filename(file.filename)
        filename = f"{timestamp}_{safe_filename}"
        
        # Save uploaded file
        uploaded_path = UPLOADS_DIR / "videos" / filename
        uploaded_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"📥 Uploading video: {filename}")
        
        with open(uploaded_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"✅ Upload complete: {os.path.getsize(uploaded_path) / 1024 / 1024:.2f} MB")
        
        # Validate video
        is_valid, message = validate_video(str(uploaded_path))
        if not is_valid:
            return JSONResponse({"error": message}, status_code=400)
        
        # Get video info
        video_info = get_video_info(str(uploaded_path))
        print(f"📊 Video: {video_info['width']}x{video_info['height']} @ {video_info['fps']:.1f}fps, {video_info['duration']:.1f}s")
        
        # Prepare output path
        output_path = None
        if generate_output:
            output_filename = f"analyzed_{timestamp}.mp4"
            output_path = str(PROCESSED_DIR / "videos" / output_filename)
        
        print("🎬 Starting video processing with full analytics...")
        
        # Process video
        result = video_processor.process_video(
            video_path=str(uploaded_path),
            output_path=output_path,
            generate_output_video=generate_output,
            export_csv=export_csv
        )
        
        # Build response
        response = {
            "status": "success",
            "video_info": {
                "filename": video_info["filename"],
                "resolution": video_info["resolution"],
                "fps": round(video_info["fps"], 2),
                "duration_seconds": round(video_info["duration"], 2),
                "total_frames": video_info["frame_count"]
            },
            "processing_time_seconds": round(result["processing_time"], 2),
            "analytics": {
                "total_visitors": result["total_tracks"],
                "conversion_rate_percent": result["summary"]["conversion_rate"],
                "avg_visit_duration_seconds": round(result["summary"]["avg_visit_duration"], 2),
                "behavior_breakdown": {
                    "purchasers": result["summary"]["purchasers"],
                    "window_shoppers": result["summary"]["window_shoppers"],
                    "browsers": result["summary"]["browsers"],
                    "passing_through": result["summary"]["passing_through"],
                    "idle": result["summary"]["idle"]
                },
                "checkout_visitors": result["summary"]["total_checkout_visitors"]
            },
            "files": {}
        }
        
        # Add file links
        if generate_output and result.get("output_video_path"):
            output_filename = Path(result["output_video_path"]).name
            response["files"]["annotated_video"] = f"/processed/videos/{output_filename}"
        
        if export_csv and result.get("csv_path"):
            csv_filename = Path(result["csv_path"]).name
            response["files"]["csv_report"] = f"/data/csv/{csv_filename}"
        
        print(f"✅ Video processing complete in {result['processing_time']:.2f}s")
        
        return response
        
    except Exception as e:
        print(f"❌ Video processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


# ----------------------------
# Quick People Count
# ----------------------------
@router.post("/count")
async def quick_count(
    file: UploadFile = File(...),
    confidence: Optional[float] = Query(None, ge=0, le=1)
):
    """
    Quick people count without full analytics
    Faster than /detect/image endpoint
    
    **Parameters:**
    - **file**: Image file
    - **confidence**: Detection threshold
    
    **Returns:**
    - people_count: Number of people detected
    """
    try:
        if detection_engine is None:
            return JSONResponse(
                {"error": "Detection engine not initialized"},
                status_code=500
            )
        
        # Read image directly
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return JSONResponse({"error": "Failed to decode image"}, status_code=400)
        
        # Quick count
        count = detection_engine.count_people(image, confidence=confidence)
        
        return {
            "status": "success",
            "people_count": count
        }
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ----------------------------
# Batch Image Detection
# ----------------------------
@router.post("/batch")
async def detect_batch(
    files: list[UploadFile] = File(...),
    confidence: Optional[float] = Query(None, ge=0, le=1)
):
    """
    Detect people in multiple images at once
    More efficient than individual requests
    
    **Parameters:**
    - **files**: Multiple image files
    - **confidence**: Detection threshold
    
    **Returns:**
    - results: Detection results for each image
    """
    try:
        if detection_engine is None:
            return JSONResponse(
                {"error": "Detection engine not initialized"},
                status_code=500
            )
        
        if len(files) > 50:
            return JSONResponse(
                {"error": "Maximum 50 images per batch"},
                status_code=400
            )
        
        # Load all images
        images = []
        filenames = []
        
        for file in files:
            content = await file.read()
            nparr = np.frombuffer(content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is not None:
                images.append(image)
                filenames.append(file.filename)
        
        # Batch detection
        all_detections = detection_engine.detect_batch(
            images,
            confidence=confidence,
            person_only=True
        )
        
        # Format results
        results = []
        for filename, detections in zip(filenames, all_detections):
            results.append({
                "filename": filename,
                "people_count": len(detections),
                "detections": [
                    {
                        "bbox": det.bbox,
                        "confidence": round(det.confidence, 3)
                    }
                    for det in detections
                ]
            })
        
        return {
            "status": "success",
            "images_processed": len(results),
            "total_people": sum(r["people_count"] for r in results),
            "results": results
        }
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    print("✅ Detection Routes Module Ready")
    print("📍 Endpoints:")
    print("  POST /detect/image - Image detection")
    print("  POST /detect/video - Video processing with analytics")
    print("  POST /detect/count - Quick people count")
    print("  POST /detect/batch - Batch image detection")