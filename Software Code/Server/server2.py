"""
Eyeora AI-CCTV Backend Server
Main FastAPI server with integrated analytics and tracking
Location: Software Code/Server/server.py
"""

import socket
import uvicorn
import psutil
import os
import cv2
import base64
import io
import numpy as np
from datetime import datetime
from pathlib import Path
from PIL import Image
from typing import Optional

from fastapi import FastAPI, Form, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import core modules
from core.config import (
    MODEL_PATH, UPLOADS_DIR, PROCESSED_DIR, STATIC_DIR,
    CONFIDENCE_THRESHOLD, MODELS_DIR
)
from core.detection_engine import DetectionEngine, ModelManager
from core.video_processor import VideoProcessor
from core.tracker import PersonTracker
from core.behavior_analyzer import BehaviorAnalyzer
from core.alert_system import AlertSystem
from core.csv_exporter import DataExporter
from utils.validators import validate_video_file, validate_image_file, sanitize_filename
from utils.video_utils import get_video_info, validate_video

# Initialize FastAPI app
app = FastAPI(
    title="Eyeora AI-CCTV API",
    description="Advanced AI-powered CCTV analytics system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Global Instances
# ----------------------------
print("🚀 Initializing Eyeora Backend...")

# Detection engine
detection_engine = None
model_manager = ModelManager()

# Video processor
video_processor = None

# Alert system
alert_system = AlertSystem()

# Data exporter
data_exporter = DataExporter()

# Live camera
camera = None

print("✅ Backend initialized")

# ----------------------------
# Initialize Detection Engine
# ----------------------------
def get_detection_engine():
    """Get or create detection engine"""
    global detection_engine
    if detection_engine is None:
        print("📦 Loading detection engine...")
        detection_engine = DetectionEngine()
    return detection_engine

def get_video_processor():
    """Get or create video processor"""
    global video_processor
    if video_processor is None:
        print("🎬 Loading video processor...")
        video_processor = VideoProcessor()
    return video_processor

# ----------------------------
# Mount static files
# ----------------------------
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ----------------------------
# Utility Functions (Original)
# ----------------------------
def lan_connected():
    """Check if connected to LAN"""
    addrs = psutil.net_if_addrs()
    for iface, details in addrs.items():
        for addr in details:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                return True
    return False

def get_ip_addresses():
    """Get all IP addresses"""
    ips = {"localhost": "127.0.0.1"}
    addrs = psutil.net_if_addrs()
    for iface, details in addrs.items():
        for addr in details:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                ips[iface] = addr.address
    return ips

# ----------------------------
# ADDITIONS: Robust IP discovery (NEW, non-breaking)
# ----------------------------
VIRTUAL_IFACE_HINTS = ("loopback", "vmware", "virtualbox", "vbox", "hyper-v", "vethernet", "docker", "br-", "lo")

def get_primary_ipv4() -> str:
    """
    Determine the primary outbound IPv4 without sending traffic.
    Works well on Windows/Linux/macOS/Docker.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No packets are sent; OS picks an outbound interface to this target
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def get_all_ipv4_filtered() -> dict:
    """
    Return a dict of iface -> IPv4 skipping loopback, virtual,
    and interfaces that are down.
    """
    ips = {"localhost": "127.0.0.1"}
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
    except Exception:
        return ips

    for iface, details in addrs.items():
        # Skip down interfaces and obvious virtuals
        if iface in stats and not stats[iface].isup:
            continue
        lname = iface.lower()
        if any(hint in lname for hint in VIRTUAL_IFACE_HINTS):
            continue

        for addr in details:
            if addr.family == socket.AF_INET:
                ip = addr.address
                if not ip.startswith("127."):
                    ips[iface] = ip
    return ips

# ----------------------------
# Frontend Routes
# ----------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main frontend HTML file"""
    index_path = Path("index.html")
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    
    # Fallback dashboard
    return """
    <html>
        <head>
            <title>Eyeora AI-CCTV</title>
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    color: #e2e8f0;
                    margin: 0;
                    padding: 20px;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 40px;
                }
                h1 {
                    color: #38bdf8;
                    text-align: center;
                    font-size: 3em;
                    margin-bottom: 10px;
                }
                .subtitle {
                    text-align: center;
                    color: #94a3b8;
                    margin-bottom: 40px;
                }
                .status-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }
                .status-card {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 20px;
                    border: 1px solid rgba(56, 189, 248, 0.2);
                }
                .status-card h3 {
                    color: #38bdf8;
                    margin-top: 0;
                }
                .feature-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                }
                .feature-card {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 25px;
                    border-left: 4px solid #38bdf8;
                }
                .feature-card h3 {
                    color: #38bdf8;
                    margin-top: 0;
                }
                .api-link {
                    display: inline-block;
                    background: #38bdf8;
                    color: #0f172a;
                    padding: 15px 30px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                    margin: 20px auto;
                    text-align: center;
                    display: block;
                    width: fit-content;
                }
                .api-link:hover {
                    background: #0ea5e9;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Eyeora AI-CCTV</h1>
                <p class="subtitle">Advanced AI-Powered CCTV Analytics System</p>
                
                <div class="status-grid">
                    <div class="status-card">
                        <h3>✅ Backend Status</h3>
                        <p>Server is running successfully!</p>
                        <p>All systems operational</p>
                    </div>
                    <div class="status-card">
                        <h3>🤖 AI Models</h3>
                        <p>YOLO11 Detection Engine</p>
                        <p>Person Tracking Active</p>
                    </div>
                    <div class="status-card">
                        <h3>📊 Analytics</h3>
                        <p>Behavior Analysis Ready</p>
                        <p>Real-time Alerts Enabled</p>
                    </div>
                </div>
                
                <h2 style="color: #38bdf8; text-align: center; margin-top: 40px;">Features</h2>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <h3>🎯 Person Detection</h3>
                        <p>Real-time person detection and counting using state-of-the-art YOLO11 model</p>
                    </div>
                    <div class="feature-card">
                        <h3>👥 Multi-Person Tracking</h3>
                        <p>Track individuals throughout their entire store visit with unique IDs</p>
                    </div>
                    <div class="feature-card">
                        <h3>🛍️ Behavior Analysis</h3>
                        <p>Automatic classification: Window Shopping, Browsing, Purchasing, Idle, Passing Through</p>
                    </div>
                    <div class="feature-card">
                        <h3>📍 Zone Detection</h3>
                        <p>Monitor entry, exit, and checkout zones with intelligent area tracking</p>
                    </div>
                    <div class="feature-card">
                        <h3>🚨 Real-time Alerts</h3>
                        <p>Crowd detection, loitering alerts, and suspicious behavior monitoring</p>
                    </div>
                    <div class="feature-card">
                        <h3>📈 Analytics & Reports</h3>
                        <p>Comprehensive CSV/JSON/Excel exports with detailed visitor statistics</p>
                    </div>
                </div>
                
                <a href="/docs" class="api-link">📖 Open API Documentation</a>
                
                <div style="text-align: center; margin-top: 40px; color: #64748b;">
                    <p>⚠️ Frontend files (index.html) not found in directory</p>
                    <p>Place your frontend files in the server directory to access the full interface</p>
                </div>
            </div>
        </body>
    </html>
    """

@app.get("/styles.css")
async def get_styles():
    """Serve CSS file"""
    css_path = Path("styles.css")
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    return JSONResponse({"error": "styles.css not found"}, status_code=404)

@app.get("/script.js")
async def get_script():
    """Serve JavaScript file"""
    js_path = Path("script.js")
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    return JSONResponse({"error": "script.js not found"}, status_code=404)

@app.get("/config", response_class=HTMLResponse)
async def config_form():
    """Wi-Fi configuration form"""
    return """
    <html>
        <body style="font-family: Arial; text-align: center; padding-top: 50px; background:#0f172a; color:#e2e8f0;">
            <h1 style="color:#facc15;">Wi-Fi Config Mode</h1>
            <form action="/connect" method="post">
              <input name="ssid" placeholder="SSID" required style="padding: 10px; margin: 5px; border-radius: 5px;"><br><br>
              <input name="password" placeholder="Password" type="password" required style="padding: 10px; margin: 5px; border-radius: 5px;"><br><br>
              <button type="submit" style="padding: 10px 30px; background: #38bdf8; border: none; border-radius: 5px; cursor: pointer;">Connect</button>
            </form>
        </body>
    </html>
    """

@app.post("/connect")
async def connect_wifi(ssid: str = Form(...), password: str = Form(...)):
    """Handle Wi-Fi connection (for ESP32)"""
    return {"status": "received", "ssid": ssid, "password": password}

# ----------------------------
# Detection Routes - Image
# ----------------------------
@app.post("/detect/image")
async def detect_image(
    file: UploadFile = File(...),
    confidence: Optional[float] = Query(None, description="Detection confidence threshold"),
    return_analytics: bool = Query(False, description="Return detailed analytics")
):
    """
    Detect people in an uploaded image
    
    - **file**: Image file (JPG, PNG)
    - **confidence**: Detection threshold (0-1)
    - **return_analytics**: Include detailed detection data
    """
    try:
        # Validate file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = sanitize_filename(file.filename)
        filename = f"{timestamp}_{safe_filename}"
        
        # Save uploaded file
        uploaded_path = UPLOADS_DIR / "images" / filename
        uploaded_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(uploaded_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"📥 Image uploaded: {uploaded_path}")
        
        # Validate image
        is_valid, message = validate_image_file(str(uploaded_path))
        if not is_valid:
            return JSONResponse({"error": message}, status_code=400)
        
        # Read image
        image = cv2.imread(str(uploaded_path))
        
        # Get detection engine
        engine = get_detection_engine()
        
        # Detect people
        detections, crops = engine.detect_people(
            image, 
            confidence=confidence,
            return_crops=return_analytics
        )
        
        print(f"✅ Detected {len(detections)} people")
        
        # Annotate image
        annotated = engine.visualize_detections(image, detections)
        
        # Save annotated image
        processed_path = PROCESSED_DIR / "images" / filename
        processed_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(processed_path), annotated)
        
        response = {
            "status": "success",
            "people_count": len(detections),
            "annotated_file": f"/processed/images/{filename}",
            "original_file": f"/uploads/images/{filename}",
            "timestamp": timestamp
        }
        
        if return_analytics:
            response["detections"] = [
                {
                    "bbox": det.bbox,
                    "confidence": det.confidence,
                    "center": det.center,
                    "area": det.area
                }
                for det in detections
            ]
        
        return response
        
    except Exception as e:
        print(f"❌ Image detection error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ----------------------------
# Detection Routes - Video with Full Analytics
# ----------------------------
@app.post("/detect/video")
async def detect_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    generate_output: bool = Query(True, description="Generate annotated output video"),
    export_csv: bool = Query(True, description="Export analytics to CSV"),
    confidence: Optional[float] = Query(None, description="Detection confidence threshold")
):
    """
    Process video with full people tracking and behavior analysis
    
    - **file**: Video file (MP4, AVI, MOV, etc.)
    - **generate_output**: Create annotated output video
    - **export_csv**: Export analytics data
    - **confidence**: Detection threshold
    """
    try:
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
        
        print(f"✅ Upload complete: {uploaded_path}")
        
        # Validate video
        is_valid, message = validate_video(str(uploaded_path))
        if not is_valid:
            return JSONResponse({"error": message}, status_code=400)
        
        # Get video info
        video_info = get_video_info(str(uploaded_path))
        print(f"📊 Video: {video_info['width']}x{video_info['height']} @ {video_info['fps']:.2f}fps")
        
        # Get video processor
        processor = get_video_processor()
        
        # Process video with full analytics
        output_path = None
        if generate_output:
            output_filename = f"analyzed_{timestamp}.mp4"
            output_path = str(PROCESSED_DIR / "videos" / output_filename)
        
        print("🎬 Starting video processing with analytics...")
        
        result = processor.process_video(
            video_path=str(uploaded_path),
            output_path=output_path,
            generate_output_video=generate_output,
            export_csv=export_csv
        )
        
        # Prepare response
        response = {
            "status": "success",
            "video_info": result["video_info"],
            "processing_time": result["processing_time"],
            "analytics": {
                "total_visitors": result["total_tracks"],
                "conversion_rate": result["summary"]["conversion_rate"],
                "avg_visit_duration": result["summary"]["avg_visit_duration"],
                "purchasers": result["summary"]["purchasers"],
                "window_shoppers": result["summary"]["window_shoppers"],
                "browsers": result["summary"]["browsers"],
                "passing_through": result["summary"]["passing_through"],
                "idle": result["summary"]["idle"]
            },
            "files": {}
        }
        
        if generate_output and result["output_video_path"]:
            output_filename = Path(result["output_video_path"]).name
            response["files"]["annotated_video"] = f"/processed/videos/{output_filename}"
        
        if export_csv and result["csv_path"]:
            csv_filename = Path(result["csv_path"]).name
            response["files"]["csv_report"] = f"/data/csv/{csv_filename}"
        
        return response
        
    except Exception as e:
        print(f"❌ Video processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

# ----------------------------
# Serve Processed Files
# ----------------------------
@app.get("/processed/images/{filename}")
async def get_processed_image(filename: str):
    """Serve processed image"""
    file_path = PROCESSED_DIR / "images" / filename
    if file_path.exists():
        return FileResponse(file_path, media_type="image/jpeg")
    return JSONResponse({"error": "File not found"}, status_code=404)

@app.get("/processed/videos/{filename}")
async def get_processed_video(filename: str):
    """Serve processed video"""
    file_path = PROCESSED_DIR / "videos" / filename
    if not file_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)
    
    media_type = "video/mp4" if filename.endswith('.mp4') else "video/x-msvideo"
    
    return FileResponse(
        file_path,
        media_type=media_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Type": media_type
        }
    )

@app.get("/data/csv/{filename}")
async def get_csv_file(filename: str):
    """Serve CSV export file"""
    from core.config import DATA_DIR
    file_path = DATA_DIR / "csv" / filename
    if file_path.exists():
        return FileResponse(file_path, media_type="text/csv")
    return JSONResponse({"error": "File not found"}, status_code=404)

# ----------------------------
# Live Camera Feed
# ----------------------------
def get_camera():
    """Get or create camera instance"""
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("⚠️ Warning: Could not open camera")
    return camera

def generate_frames():
    """Generate frames for live stream"""
    cam = get_camera()
    while True:
        success, frame = cam.read()
        if not success:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

@app.get("/video_feed")
def video_feed():
    """Live camera stream endpoint"""
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# ----------------------------
# Live Detection (Frame-by-frame)
# ----------------------------
@app.post("/detect/frame")
async def detect_frame(data: dict):
    """
    Detect people in a single frame (for live detection)
    Receives base64 encoded image
    """
    try:
        # Decode base64 image
        img_data = base64.b64decode(data["image"].split(",")[1])
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        img_array = np.array(img)
        
        # Get detection engine
        engine = get_detection_engine()
        
        # Detect people only
        detections, _ = engine.detect_people(img_array)
        
        # Format response
        detection_list = []
        for det in detections:
            detection_list.append({
                "class": det.class_name,
                "confidence": float(det.confidence),
                "bbox": det.bbox,
                "center": det.center
            })
        
        return {
            "success": True,
            "people_count": len(detections),
            "detections": detection_list
        }
        
    except Exception as e:
        print(f"❌ Frame detection error: {str(e)}")
        return {"error": str(e), "detections": []}

# ----------------------------
# Analytics Endpoints
# ----------------------------
@app.get("/analytics/summary")
async def get_analytics_summary():
    """Get current analytics summary"""
    # This would typically query from a database
    # For now, return a placeholder
    return {
        "total_visitors_today": 0,
        "conversion_rate": 0.0,
        "avg_visit_duration": 0.0,
        "active_alerts": len(alert_system.get_active_alerts())
    }

@app.get("/analytics/alerts")
async def get_alerts(
    active_only: bool = Query(True, description="Only show active alerts"),
    limit: int = Query(50, description="Maximum alerts to return")
):
    """Get alerts from alert system"""
    if active_only:
        alerts = alert_system.get_active_alerts()
    else:
        alerts = alert_system.get_alert_history(limit=limit)
    
    return {
        "alerts": [alert.to_dict() for alert in alerts],
        "count": len(alerts),
        "statistics": alert_system.get_statistics()
    }

# ----------------------------
# System Status
# ----------------------------
@app.get("/status")
async def system_status():
    """Get system status and information"""
    return {
        "status": "online",
        "modules": {
            "detection_engine": detection_engine is not None,
            "video_processor": video_processor is not None,
            "alert_system": True,
            "data_exporter": True
        },
        "model_info": detection_engine.get_model_info() if detection_engine else None,
        "ip_addresses": get_ip_addresses(),
        "lan_connected": lan_connected()
    }

# ----------------------------
# ADDITION: Quick IP endpoint (NEW)
# ----------------------------
@app.get("/ip")
async def ip_info():
    """Return primary and filtered interface IPv4s"""
    return {
        "primary_ipv4": get_primary_ipv4(),
        "all_ipv4_filtered": get_all_ipv4_filtered(),
        "all_ipv4_raw": get_ip_addresses(),
        "lan_connected": lan_connected()
    }

# ----------------------------
# Health Check
# ----------------------------
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ----------------------------
# Run Server
# ----------------------------
if __name__ == "__main__":
    port = 8000

    # ---- ADDITIONAL logging (NEW) ----
    primary_ip = get_primary_ipv4()
    filtered_ips = get_all_ipv4_filtered()

    print("\n" + "="*70)
    print("🌐 Network Discovery")
    print("="*70)
    if primary_ip != "127.0.0.1":
        print(f"📡 Primary LAN (recommended): http://{primary_ip}:{port}")
    else:
        print("📡 Primary LAN: (not detected; are you on a network?)")
    for iface, ip in filtered_ips.items():
        if iface != "localhost":
            print(f"📡 {iface:12s} ->  http://{ip}:{port}")
    print("="*70 + "\n")
    # ---- END additions ----

    # ---- Original startup print logic (UNCHANGED) ----
    ips = get_ip_addresses()
    
    print("\n" + "="*70)
    print("🚀 EYEORA AI-CCTV BACKEND SERVER")
    print("="*70)
    print(f"📡 Local access:     http://127.0.0.1:{port}")
    for iface, ip in ips.items():
        if iface != "localhost":
            print(f"📡 Network ({iface:8s}): http://{ip}:{port}")
    print(f"📖 API Docs:         http://127.0.0.1:{port}/docs")
    print(f"📊 System Status:    http://127.0.0.1:{port}/status")
    print("="*70)
    print("\n✨ Features Enabled:")
    print("  ✅ Person Detection & Tracking")
    print("  ✅ Behavior Analysis (5 types)")
    print("  ✅ Zone Detection (Entry/Exit/Checkout)")
    print("  ✅ Real-time Alerts")
    print("  ✅ CSV/JSON/Excel Export")
    print("  ✅ Live Camera Feed")
    print("  ✅ Video Processing with Analytics")
    print("\n💡 Tips:")
    print("  • Place index.html in this directory for custom frontend")
    print("  • Upload videos to /detect/video for full analytics")
    print("  • Check /docs for complete API documentation")
    print("\n" + "="*70 + "\n")
    
    # Bind to all interfaces so other devices can reach it
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
