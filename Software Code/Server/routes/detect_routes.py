from fastapi import APIRouter, UploadFile, File
import os, shutil
from ml.yolo_model import detect_image

router = APIRouter()

# Ensure folders exist
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/results", exist_ok=True)

@router.post("/detect/image")
async def detect_image_api(file: UploadFile = File(...)):
    input_path = f"uploads/images/{file.filename}"
    output_path = f"uploads/results/{file.filename}"

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = detect_image(input_path, output_path)

    detections = [
        {
            "class": result.names[int(box.cls)],
            "confidence": float(box.conf),
            "bbox": box.xyxy.tolist()[0],
        }
        for box in result.boxes
    ]

    return {
        "status": "success",
        "annotated_file": f"/uploads/results/{file.filename}",
        "detections": detections
    }
