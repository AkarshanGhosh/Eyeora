import socket
import uvicorn
import psutil
import os
import cv2
import base64
import io
import numpy as np
from datetime import datetime
from PIL import Image

from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

app = FastAPI()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Load YOLO Model Once
# ----------------------------
MODEL_PATH = "models/yolo11x.pt"

# Download model if it doesn't exist
if not os.path.exists(MODEL_PATH):
    print(f"⬇️ Downloading {MODEL_PATH}...")
    os.makedirs("models", exist_ok=True)
    model = YOLO("yolo11x.pt")
    model.save(MODEL_PATH)
else:
    model = YOLO(MODEL_PATH)

print(f"✅ Loaded model: {MODEL_PATH}")
print(f"📊 Model can detect {len(model.names)} classes: {list(model.names.values())[:10]}...")

# ----------------------------
# Ensure folders exist
# ----------------------------
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)
os.makedirs("processed/images", exist_ok=True)
os.makedirs("processed/videos", exist_ok=True)

# ----------------------------
# Utility: check LAN connection
# ----------------------------
def lan_connected():
    addrs = psutil.net_if_addrs()
    for iface, details in addrs.items():
        for addr in details:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                return True
    return False

# ----------------------------
# Utility: get IP addresses
# ----------------------------
def get_ip_addresses():
    ips = {"localhost": "127.0.0.1"}
    addrs = psutil.net_if_addrs()
    for iface, details in addrs.items():
        for addr in details:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                ips[iface] = addr.address
    return ips

# ----------------------------
# Root
# ----------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    if lan_connected():
        return """
        <html>
            <body style="font-family: Arial; text-align: center; padding-top: 50px; background:#0f172a; color:#e2e8f0;">
                <h1 style="color:#38bdf8;">🚀 Eyeora Backend Running</h1>
                <p>Connected ✅</p>
                <p>Check API Docs: <a href="/docs" style="color:#38bdf8;">Swagger UI</a></p>
            </body>
        </html>
        """
    else:
        return RedirectResponse(url="/config")


@app.get("/config", response_class=HTMLResponse)
async def config_form():
    return """
    <html>
        <body style="font-family: Arial; text-align: center; padding-top: 50px; background:#0f172a; color:#e2e8f0;">
            <h1 style="color:#facc15;">Wi-Fi Config Mode</h1>
            <form action="/connect" method="post">
              <input name="ssid" placeholder="SSID" required><br><br>
              <input name="password" placeholder="Password" type="password" required><br><br>
              <button type="submit">Connect</button>
            </form>
        </body>
    </html>
    """

@app.post("/connect")
async def connect_wifi(ssid: str = Form(...), password: str = Form(...)):
    return {"status": "received", "ssid": ssid, "password": password}

# ----------------------------
# Detect Image
# ----------------------------
@app.post("/detect/image")
async def detect_image(file: UploadFile = File(...)):
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    uploaded_path = os.path.join("uploads/images", filename)

    with open(uploaded_path, "wb") as f:
        f.write(await file.read())

    # Run detection
    results = model(uploaded_path, conf=0.25, iou=0.45)
    
    # Get annotated image
    annotated = results[0].plot()
    processed_path = os.path.join("processed/images", filename)
    cv2.imwrite(processed_path, annotated)

    return {"status": "success", "annotated_file": f"/processed/images/{filename}"}

# ----------------------------
# Serve Processed Images
# ----------------------------
@app.get("/processed/images/{filename}")
async def get_processed_image(filename: str):
    file_path = os.path.join("processed/images", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/jpeg")
    return JSONResponse({"error": "File not found"}, status_code=404)

# ----------------------------
# Detect Video - FIXED VERSION
# ----------------------------
@app.post("/detect/video")
async def detect_video(file: UploadFile = File(...)):
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = file.filename
        safe_filename = "".join(c for c in original_filename if c.isalnum() or c in "._- ")
        
        filename = f"{timestamp}_{safe_filename}"
        uploaded_path = os.path.join("uploads/videos", filename)
        
        output_filename = f"detected_{timestamp}.mp4"
        output_path = os.path.join("processed/videos", output_filename)

        print(f"Saving uploaded video to: {uploaded_path}")
        
        # Save uploaded video
        with open(uploaded_path, "wb") as f:
            content = await file.read()
            f.write(content)

        print(f"Processing video: {uploaded_path}")

        # Open video file
        cap = cv2.VideoCapture(uploaded_path)
        
        if not cap.isOpened():
            return JSONResponse({"error": "Could not open video file"}, status_code=400)
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0 or fps > 120:
            fps = 30
            
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video properties: {width}x{height} @ {fps}fps, {total_frames} frames")
        
        # Use MP4V codec - most compatible with browsers without external tools
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            cap.release()
            return JSONResponse({"error": "Could not initialize video writer"}, status_code=500)
        
        frame_count = 0
        
        print("Starting frame processing...")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run detection on frame
            results = model(frame, conf=0.25, iou=0.45, verbose=False)
            annotated_frame = results[0].plot()
            
            # Write frame
            out.write(annotated_frame)
            
            frame_count += 1
            if frame_count % 30 == 0:
                print(f"Processed {frame_count}/{total_frames} frames ({int(frame_count/total_frames*100)}%)")

        cap.release()
        out.release()
        
        print(f"✅ Video processing complete: {output_path}")
        print(f"📦 Output file size: {os.path.getsize(output_path)} bytes")

        return {
            "status": "success", 
            "annotated_file": f"/processed/videos/{output_filename}",
            "frames_processed": frame_count,
            "video_info": {
                "width": width,
                "height": height,
                "fps": fps,
                "total_frames": frame_count
            }
        }
        
    except Exception as e:
        print(f"❌ Error processing video: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

# ----------------------------
# Serve Processed Videos - FIXED VERSION
# ----------------------------
@app.get("/processed/videos/{filename}")
async def get_processed_video(filename: str):
    file_path = os.path.join("processed/videos", filename)
    if not os.path.exists(file_path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    
    file_size = os.path.getsize(file_path)
    print(f"📹 Serving video: {filename} ({file_size} bytes)")
    
    return FileResponse(
        file_path, 
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Type": "video/mp4",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# ----------------------------
# Live Stream
# ----------------------------
camera = None

def get_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("Warning: Could not open camera")
    return camera

def generate_frames():
    cam = get_camera()
    while True:
        success, frame = cam.read()
        if not success:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

# ----------------------------
# Detect Per Frame (Live Detection)
# ----------------------------
@app.post("/detect/frame")
async def detect_frame(data: dict):
    try:
        # Decode base64 image
        img_data = base64.b64decode(data["image"].split(",")[1])
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        img_array = np.array(img)

        # Run detection
        results = model(img_array, conf=0.25, iou=0.45, verbose=False)

        # Extract detections
        detections = []
        for box in results[0].boxes:
            detections.append({
                "class": results[0].names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy.tolist()[0]
            })

        return {"detections": detections}
        
    except Exception as e:
        print(f"Frame detection error: {str(e)}")
        return {"error": str(e), "detections": []}

# ----------------------------
# Run Server
# ----------------------------
if __name__ == "__main__":
    port = 8000
    ips = get_ip_addresses()

    print("\n🚀 FastAPI server is starting...")
    print(f"👉 Local access: http://127.0.0.1:{port}")
    for iface, ip in ips.items():
        if iface != "localhost":
            print(f"👉 Network access ({iface}): http://{ip}:{port}")
    print(f"👉 API Docs: http://127.0.0.1:{port}/docs\n")

    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)