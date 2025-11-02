import socket
import uvicorn
import psutil
import os
import cv2
from datetime import datetime
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from ultralytics import YOLO

app = FastAPI()

# ----------------------------
# Load YOLO Model Once
# ----------------------------
MODEL_PATH = "models/yolov8n.pt"   # change if using another checkpoint
model = YOLO(MODEL_PATH)

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
# Routes
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
# Upload + YOLO Process (Image)
# ----------------------------
@app.post("/process_image")
async def process_image(file: UploadFile = File(...)):
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    uploaded_path = os.path.join("uploads/images", filename)

    with open(uploaded_path, "wb") as f:
        f.write(await file.read())

    results = model(uploaded_path)
    processed_path = os.path.join("processed/images", filename)
    results[0].save(processed_path)

    return JSONResponse({
        "status": "success",
        "uploaded": uploaded_path,
        "processed": processed_path
    })

# ----------------------------
# Upload + YOLO Process (Video)
# ----------------------------
@app.post("/process_video")
async def process_video(file: UploadFile = File(...)):
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    uploaded_path = os.path.join("uploads/videos", filename)

    with open(uploaded_path, "wb") as f:
        f.write(await file.read())

    results = model(uploaded_path, save=True)
    processed_path = results[0].save_dir  # YOLO exports full folder

    return JSONResponse({
        "status": "success",
        "uploaded": uploaded_path,
        "processed_output_folder": processed_path
    })
    
#----------------------------
#  Live Video Stream Endpoint (Placeholder)
#----------------------------
@app.post("/live_infer")
async def live_infer(frame: UploadFile = File(...)):
    img = Image.open(frame.file).convert("RGB")
    img = np.array(img)

    results = yolo_model(img, stream=True)

    detections = []
    for r in results:
        for box in r.boxes.xyxy:
            x1, y1, x2, y2 = map(int, box[:4])
            detections.append({"x": x1, "y": y1, "w": x2-x1, "h": y2-y1, "label": "object"})

    return {"boxes": detections}

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
