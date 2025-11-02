from ultralytics import YOLO

# Load YOLO model 
model = YOLO("yolov8n.pt")

def detect_image(input_path: str, output_path: str):
    """
    Run YOLO detection on an image and save annotated result.
    """
    results = model(input_path)
    results[0].save(output_path)
    return results[0]
