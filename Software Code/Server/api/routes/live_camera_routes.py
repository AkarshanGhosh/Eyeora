"""
Live Camera API Routes
Handles real-time camera streaming and control
Location: Software Code/Server/routes/live_camera_routes.py
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Dict, List
import cv2
import json
import asyncio
import numpy as np
from datetime import datetime

from core.live_camera import LiveCameraSystem

# Create router
router = APIRouter(prefix="/live", tags=["Live Camera"])

# Global camera instance (singleton)
active_cameras: Dict[int, LiveCameraSystem] = {}
websocket_clients: List[WebSocket] = []


# ==================== Camera Control ====================

@router.post("/camera/start")
async def start_camera(
    camera_index: int = Query(0, description="Camera device index"),
    enable_pose: bool = Query(False, description="Enable pose estimation"),
    enable_clothing: bool = Query(True, description="Enable clothing classification"),
    enable_tracking: bool = Query(True, description="Enable person tracking"),
    enable_objects: bool = Query(True, description="Enable object detection")
):
    """
    Start live camera with specified configuration
    
    - **camera_index**: Camera device (0 for default)
    - **enable_pose**: Enable pose estimation (reduces FPS)
    - **enable_clothing**: Enable clothing color detection
    - **enable_tracking**: Enable multi-person tracking
    - **enable_objects**: Enable object detection
    """
    try:
        # Check if camera already running
        if camera_index in active_cameras:
            return JSONResponse({
                "status": "already_running",
                "message": f"Camera {camera_index} is already active",
                "camera_id": camera_index
            })
        
        # Initialize camera
        camera = LiveCameraSystem(
            camera_index=camera_index,
            enable_pose=enable_pose,
            enable_clothing=enable_clothing,
            enable_tracking=enable_tracking,
            enable_objects=enable_objects
        )
        
        # Start camera
        if not camera.start():
            raise HTTPException(status_code=500, detail="Failed to start camera")
        
        # Store camera instance
        active_cameras[camera_index] = camera
        
        return {
            "status": "success",
            "message": "Camera started successfully",
            "camera_id": camera_index,
            "config": {
                "pose": enable_pose,
                "clothing": enable_clothing,
                "tracking": enable_tracking,
                "objects": enable_objects
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/camera/stop")
async def stop_camera(camera_index: int = Query(0, description="Camera device index")):
    """
    Stop live camera
    
    - **camera_index**: Camera device to stop
    """
    try:
        if camera_index not in active_cameras:
            raise HTTPException(status_code=404, detail=f"Camera {camera_index} not found")
        
        # Stop camera
        camera = active_cameras[camera_index]
        camera.stop()
        
        # Remove from active cameras
        del active_cameras[camera_index]
        
        return {
            "status": "success",
            "message": "Camera stopped successfully",
            "camera_id": camera_index
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/camera/status")
async def get_camera_status(camera_index: int = Query(0, description="Camera device index")):
    """
    Get camera status and configuration
    """
    try:
        if camera_index not in active_cameras:
            return {
                "status": "inactive",
                "camera_id": camera_index,
                "is_running": False
            }
        
        camera = active_cameras[camera_index]
        
        return {
            "status": "active",
            "camera_id": camera_index,
            "is_running": camera.is_running,
            "config": {
                "pose_enabled": camera.pose_estimator is not None,
                "clothing_enabled": camera.clothing_classifier is not None,
                "tracking_enabled": camera.tracker is not None,
                "objects_enabled": camera.show_objects
            },
            "display": {
                "show_detections": camera.show_detections,
                "show_pose": camera.show_pose,
                "show_stats": camera.show_stats,
                "show_objects": camera.show_objects
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Statistics ====================

@router.get("/statistics")
async def get_statistics(camera_index: int = Query(0, description="Camera device index")):
    """
    Get real-time statistics from camera
    
    Returns:
    - FPS
    - People count
    - Objects detected
    - Person details (ID, activity, clothing, nearby objects)
    """
    try:
        if camera_index not in active_cameras:
            raise HTTPException(status_code=404, detail=f"Camera {camera_index} not active")
        
        camera = active_cameras[camera_index]
        stats = camera.get_statistics()
        
        return {
            "status": "success",
            "camera_id": camera_index,
            "timestamp": datetime.now().isoformat(),
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Display Controls ====================

@router.post("/display/toggle/{feature}")
async def toggle_display_feature(
    feature: str,
    camera_index: int = Query(0, description="Camera device index")
):
    """
    Toggle display features
    
    - **feature**: detections, pose, stats, objects
    """
    try:
        if camera_index not in active_cameras:
            raise HTTPException(status_code=404, detail=f"Camera {camera_index} not active")
        
        camera = active_cameras[camera_index]
        
        # Toggle feature
        if feature == "detections":
            state = camera.toggle_detections()
        elif feature == "pose":
            state = camera.toggle_pose()
        elif feature == "stats":
            state = camera.toggle_stats()
        elif feature == "objects":
            state = camera.toggle_objects()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown feature: {feature}")
        
        return {
            "status": "success",
            "feature": feature,
            "state": state,
            "message": f"{feature} {'enabled' if state else 'disabled'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Video Streaming ====================

def generate_frames(camera_index: int = 0):
    """Generate frames for MJPEG streaming"""
    if camera_index not in active_cameras:
        return
    
    camera = active_cameras[camera_index]
    
    while camera.is_running:
        # Read and process frame
        ret, frame = camera.read_frame()
        if not ret:
            break
        
        # Process frame
        processed = camera.process_frame(frame)
        
        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', processed, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        
        frame_bytes = buffer.tobytes()
        
        # Yield frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@router.get("/stream")
async def video_stream(camera_index: int = Query(0, description="Camera device index")):
    """
    MJPEG video stream endpoint
    
    Access via: <img src="http://localhost:8000/live/stream?camera_index=0">
    """
    if camera_index not in active_cameras:
        raise HTTPException(status_code=404, detail=f"Camera {camera_index} not active")
    
    return StreamingResponse(
        generate_frames(camera_index),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# ==================== WebSocket for Real-time Updates ====================

@router.websocket("/ws/statistics")
async def websocket_statistics(websocket: WebSocket, camera_index: int = 0):
    """
    WebSocket endpoint for real-time statistics updates
    
    Sends statistics every 500ms
    """
    await websocket.accept()
    websocket_clients.append(websocket)
    
    try:
        while True:
            if camera_index in active_cameras:
                camera = active_cameras[camera_index]
                stats = camera.get_statistics()
                
                await websocket.send_json({
                    "type": "statistics",
                    "timestamp": datetime.now().isoformat(),
                    "data": stats
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": "Camera not active"
                })
            
            await asyncio.sleep(0.5)  # Update every 500ms
            
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)
        print(f"WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_clients.remove(websocket)


@router.websocket("/ws/frames")
async def websocket_frames(websocket: WebSocket, camera_index: int = 0):
    """
    WebSocket endpoint for frame streaming
    
    Sends processed frames as base64 encoded images
    """
    await websocket.accept()
    
    try:
        if camera_index not in active_cameras:
            await websocket.send_json({
                "type": "error",
                "message": "Camera not active"
            })
            return
        
        camera = active_cameras[camera_index]
        
        while camera.is_running:
            # Read and process frame
            ret, frame = camera.read_frame()
            if not ret:
                continue
            
            processed = camera.process_frame(frame)
            
            # Encode as JPEG
            ret, buffer = cv2.imencode('.jpg', processed, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not ret:
                continue
            
            # Convert to base64
            import base64
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Send frame
            await websocket.send_json({
                "type": "frame",
                "timestamp": datetime.now().isoformat(),
                "frame": frame_base64
            })
            
            await asyncio.sleep(0.033)  # ~30 FPS
            
    except WebSocketDisconnect:
        print("Frame WebSocket client disconnected")
    except Exception as e:
        print(f"Frame WebSocket error: {e}")


# ==================== Person Details ====================

@router.get("/persons")
async def get_persons(camera_index: int = Query(0, description="Camera device index")):
    """
    Get all tracked persons with details
    """
    try:
        if camera_index not in active_cameras:
            raise HTTPException(status_code=404, detail=f"Camera {camera_index} not active")
        
        camera = active_cameras[camera_index]
        stats = camera.get_statistics()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "people_count": stats['people_detected'],
            "persons": stats['live_persons']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/persons/{person_id}")
async def get_person_details(
    person_id: int,
    camera_index: int = Query(0, description="Camera device index")
):
    """
    Get details for a specific person
    """
    try:
        if camera_index not in active_cameras:
            raise HTTPException(status_code=404, detail=f"Camera {camera_index} not active")
        
        camera = active_cameras[camera_index]
        
        # Find person
        if person_id in camera.live_persons:
            person = camera.live_persons[person_id]
            
            return {
                "status": "success",
                "person_id": person_id,
                "data": {
                    "id": person.track_id,
                    "duration": person.duration,
                    "activity": person.dominant_activity,
                    "clothing": person.clothing,
                    "is_moving": person.is_moving,
                    "nearby_objects": list(person.detected_objects),
                    "first_seen": person.first_seen,
                    "last_seen": person.last_seen,
                    "position_count": len(person.positions)
                }
            }
        else:
            raise HTTPException(status_code=404, detail=f"Person {person_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Objects ====================

@router.get("/objects")
async def get_objects(camera_index: int = Query(0, description="Camera device index")):
    """
    Get all detected objects
    """
    try:
        if camera_index not in active_cameras:
            raise HTTPException(status_code=404, detail=f"Camera {camera_index} not active")
        
        camera = active_cameras[camera_index]
        stats = camera.get_statistics()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "objects_count": stats['objects_detected'],
            "objects": stats['objects']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Snapshot ====================

@router.get("/snapshot")
async def take_snapshot(
    camera_index: int = Query(0, description="Camera device index"),
    include_overlay: bool = Query(True, description="Include detection overlays")
):
    """
    Take a snapshot from live camera
    
    Returns base64 encoded image
    """
    try:
        if camera_index not in active_cameras:
            raise HTTPException(status_code=404, detail=f"Camera {camera_index} not active")
        
        camera = active_cameras[camera_index]
        
        # Get current frame
        if include_overlay and camera.processed_frame is not None:
            frame = camera.processed_frame
        elif camera.current_frame is not None:
            frame = camera.current_frame
        else:
            raise HTTPException(status_code=503, detail="No frame available")
        
        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not ret:
            raise HTTPException(status_code=500, detail="Failed to encode frame")
        
        # Convert to base64
        import base64
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "image": f"data:image/jpeg;base64,{image_base64}",
            "with_overlay": include_overlay
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Health Check ====================

@router.get("/health")
async def health_check():
    """
    Check live camera system health
    """
    return {
        "status": "healthy",
        "active_cameras": len(active_cameras),
        "camera_indices": list(active_cameras.keys()),
        "websocket_clients": len(websocket_clients),
        "timestamp": datetime.now().isoformat()
    }