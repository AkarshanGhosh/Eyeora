from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import os
from datetime import datetime

router = APIRouter()

# Ensure folders exist
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)

# ----------------------------
# Upload Image Endpoint
# ----------------------------
@router.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join("uploads/images", filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())
    return JSONResponse({"status": "success", "filename": filename})

# ----------------------------
# Upload Video Endpoint
# ----------------------------
@router.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join("uploads/videos", filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())
    return JSONResponse({"status": "success", "filename": filename})
