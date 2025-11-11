"""
Video Utilities - Helper functions for video processing
Location: Software Code/Server/utils/video_utils.py
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict
import time


def get_video_info(video_path: str) -> Dict:
    """
    Get video file information
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dictionary with video information
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    info = {
        "filename": Path(video_path).name,
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    }
    
    info["duration"] = info["frame_count"] / info["fps"] if info["fps"] > 0 else 0
    info["resolution"] = f"{info['width']}x{info['height']}"
    
    cap.release()
    
    return info


def validate_video(video_path: str) -> Tuple[bool, str]:
    """
    Validate if video file is readable
    
    Args:
        video_path: Path to video
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(video_path)
    
    # Check if file exists
    if not path.exists():
        return False, "Video file not found"
    
    # Check file extension
    valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    if path.suffix.lower() not in valid_extensions:
        return False, f"Unsupported video format. Supported: {', '.join(valid_extensions)}"
    
    # Try to open video
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return False, "Could not open video file"
        
        # Try to read first frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return False, "Could not read video frames"
        
        return True, "Valid video file"
    
    except Exception as e:
        return False, f"Video validation error: {str(e)}"


def resize_frame(
    frame: np.ndarray,
    width: int = None,
    height: int = None,
    keep_aspect: bool = True
) -> np.ndarray:
    """
    Resize frame to specified dimensions
    
    Args:
        frame: Input frame
        width: Target width
        height: Target height
        keep_aspect: Maintain aspect ratio
        
    Returns:
        Resized frame
    """
    h, w = frame.shape[:2]
    
    if width is None and height is None:
        return frame
    
    if keep_aspect:
        if width is not None:
            aspect = width / w
            height = int(h * aspect)
        elif height is not None:
            aspect = height / h
            width = int(w * aspect)
    else:
        if width is None:
            width = w
        if height is None:
            height = h
    
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)


def extract_frames(
    video_path: str,
    output_dir: str,
    interval: int = 30,
    max_frames: int = None
) -> int:
    """
    Extract frames from video at specified interval
    
    Args:
        video_path: Path to video
        output_dir: Directory to save frames
        interval: Frame interval (extract every Nth frame)
        max_frames: Maximum number of frames to extract
        
    Returns:
        Number of frames extracted
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    extracted = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % interval == 0:
            filename = output_path / f"frame_{frame_count:06d}.jpg"
            cv2.imwrite(str(filename), frame)
            extracted += 1
            
            if max_frames and extracted >= max_frames:
                break
        
        frame_count += 1
    
    cap.release()
    print(f"✅ Extracted {extracted} frames to {output_dir}")
    
    return extracted


def create_video_from_frames(
    frame_dir: str,
    output_path: str,
    fps: float = 30.0,
    frame_pattern: str = "frame_*.jpg"
) -> bool:
    """
    Create video from image frames
    
    Args:
        frame_dir: Directory containing frames
        output_path: Output video path
        fps: Frames per second
        frame_pattern: Filename pattern for frames
        
    Returns:
        Success status
    """
    from glob import glob
    
    frame_files = sorted(glob(str(Path(frame_dir) / frame_pattern)))
    
    if not frame_files:
        print("⚠️  No frames found")
        return False
    
    # Read first frame to get dimensions
    first_frame = cv2.imread(frame_files[0])
    height, width = first_frame.shape[:2]
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    for frame_file in frame_files:
        frame = cv2.imread(frame_file)
        out.write(frame)
    
    out.release()
    print(f"✅ Video created: {output_path}")
    
    return True


def add_timestamp_overlay(
    frame: np.ndarray,
    timestamp: float,
    position: str = "top-left"
) -> np.ndarray:
    """
    Add timestamp overlay to frame
    
    Args:
        frame: Input frame
        timestamp: Timestamp in seconds
        position: Position ("top-left", "top-right", "bottom-left", "bottom-right")
        
    Returns:
        Frame with timestamp
    """
    from datetime import datetime, timedelta
    
    # Format timestamp
    time_str = str(timedelta(seconds=int(timestamp)))
    
    # Get text size
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    (text_width, text_height), baseline = cv2.getTextSize(
        time_str, font, font_scale, thickness
    )
    
    # Calculate position
    h, w = frame.shape[:2]
    margin = 10
    
    if position == "top-left":
        x, y = margin, margin + text_height
    elif position == "top-right":
        x, y = w - text_width - margin, margin + text_height
    elif position == "bottom-left":
        x, y = margin, h - margin
    else:  # bottom-right
        x, y = w - text_width - margin, h - margin
    
    # Draw background
    cv2.rectangle(
        frame,
        (x - 5, y - text_height - 5),
        (x + text_width + 5, y + baseline + 5),
        (0, 0, 0),
        -1
    )
    
    # Draw text
    cv2.putText(
        frame, time_str,
        (x, y),
        font, font_scale,
        (255, 255, 255),
        thickness
    )
    
    return frame


def calculate_video_quality(frame: np.ndarray) -> Dict:
    """
    Calculate basic video quality metrics
    
    Args:
        frame: Input frame
        
    Returns:
        Dictionary with quality metrics
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Calculate metrics
    brightness = np.mean(gray)
    contrast = np.std(gray)
    
    # Blur detection (Laplacian variance)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    sharpness = np.var(laplacian)
    
    return {
        "brightness": float(brightness),
        "contrast": float(contrast),
        "sharpness": float(sharpness),
        "is_blurry": sharpness < 100,  # Threshold for blur
        "is_dark": brightness < 50,
        "is_bright": brightness > 200
    }


def draw_fps(frame: np.ndarray, fps: float) -> np.ndarray:
    """
    Draw FPS counter on frame
    
    Args:
        frame: Input frame
        fps: FPS value
        
    Returns:
        Frame with FPS overlay
    """
    text = f"FPS: {fps:.1f}"
    cv2.putText(
        frame, text,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7, (0, 255, 0), 2
    )
    return frame


class FPSCounter:
    """Real-time FPS counter"""
    
    def __init__(self, avg_frames: int = 30):
        self.avg_frames = avg_frames
        self.frame_times = []
        self.last_time = time.time()
    
    def update(self) -> float:
        """Update and return current FPS"""
        current_time = time.time()
        frame_time = current_time - self.last_time
        self.last_time = current_time
        
        self.frame_times.append(frame_time)
        
        # Keep only recent frames
        if len(self.frame_times) > self.avg_frames:
            self.frame_times.pop(0)
        
        # Calculate FPS
        if len(self.frame_times) > 0:
            avg_time = sum(self.frame_times) / len(self.frame_times)
            return 1.0 / avg_time if avg_time > 0 else 0
        
        return 0
    
    def reset(self):
        """Reset counter"""
        self.frame_times.clear()
        self.last_time = time.time()


def compress_video(
    input_path: str,
    output_path: str,
    scale: float = 0.5,
    quality: int = 23
) -> bool:
    """
    Compress video file
    
    Args:
        input_path: Input video path
        output_path: Output video path
        scale: Scale factor (0.5 = 50% size)
        quality: Quality (lower = better quality, 23 is good)
        
    Returns:
        Success status
    """
    try:
        import subprocess
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-vf', f'scale=iw*{scale}:ih*{scale}',
            '-c:v', 'libx264',
            '-crf', str(quality),
            '-preset', 'medium',
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Video compressed: {output_path}")
        return True
    
    except Exception as e:
        print(f"⚠️  Compression failed: {e}")
        return False


if __name__ == "__main__":
    print("✅ Video Utilities Module Ready")
    print("🎬 Available functions:")
    print("  - get_video_info()")
    print("  - validate_video()")
    print("  - resize_frame()")
    print("  - extract_frames()")
    print("  - add_timestamp_overlay()")
    print("  - FPSCounter class")