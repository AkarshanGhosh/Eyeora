import socket
import uvicorn
import psutil
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import os
from datetime import datetime

app = FastAPI()

# ----------------------------
# Utility: check if LAN/WiFi connected
# ----------------------------
def lan_connected():
    addrs = psutil.net_if_addrs()
    for iface, details in addrs.items():
        for addr in details:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                return True
    return False

# ----------------------------
# Utility: get local IPs
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
    # For now just echo
    return {"status": "received", "ssid": ssid, "password": password}

# ----------------------------
# Upload Endpoints
# ----------------------------
# Ensure upload folders exist
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)

@app.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join("uploads/images", filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())
    return JSONResponse({"status": "success", "filename": filename})

@app.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join("uploads/videos", filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())
    return JSONResponse({"status": "success", "filename": filename})

# ----------------------------
# Run Server
# ----------------------------
if __name__ == "__main__":
    port = 8000
    ips = get_ip_addresses()

    print("\n🚀 FastAPI server is starting...")
    print(f"👉 Local access (laptop/browser only): http://127.0.0.1:{port}")
    for iface, ip in ips.items():
        if iface != "localhost":
            print(f"👉 Network access ({iface}): http://{ip}:{port}")
    print(f"👉 API Docs: http://127.0.0.1:{port}/docs\n")

    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
