"""
Input Validators - Validation functions for API inputs
Location: Software Code/Server/utils/validators.py
"""

import re
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime

from core.config import MAX_VIDEO_SIZE_MB, MAX_IMAGE_SIZE_MB


def validate_file_size(file_path: str, max_size_mb: int) -> Tuple[bool, str]:
    """
    Validate file size
    
    Args:
        file_path: Path to file
        max_size_mb: Maximum size in MB
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            return False, f"File too large: {file_size_mb:.1f}MB (max: {max_size_mb}MB)"
        
        return True, f"File size OK: {file_size_mb:.1f}MB"
    
    except Exception as e:
        return False, f"Error checking file size: {str(e)}"


def validate_video_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate video file
    
    Args:
        file_path: Path to video
        
    Returns:
        Tuple of (is_valid, message)
    """
    path = Path(file_path)
    
    # Check if exists
    if not path.exists():
        return False, "File does not exist"
    
    # Check extension
    valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
    if path.suffix.lower() not in valid_extensions:
        return False, f"Invalid video format. Allowed: {', '.join(valid_extensions)}"
    
    # Check file size
    is_valid, message = validate_file_size(file_path, MAX_VIDEO_SIZE_MB)
    if not is_valid:
        return False, message
    
    return True, "Valid video file"


def validate_image_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate image file
    
    Args:
        file_path: Path to image
        
    Returns:
        Tuple of (is_valid, message)
    """
    path = Path(file_path)
    
    # Check if exists
    if not path.exists():
        return False, "File does not exist"
    
    # Check extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
    if path.suffix.lower() not in valid_extensions:
        return False, f"Invalid image format. Allowed: {', '.join(valid_extensions)}"
    
    # Check file size
    is_valid, message = validate_file_size(file_path, MAX_IMAGE_SIZE_MB)
    if not is_valid:
        return False, message
    
    return True, "Valid image file"


def validate_confidence_threshold(confidence: float) -> Tuple[bool, str]:
    """
    Validate confidence threshold
    
    Args:
        confidence: Confidence value
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not isinstance(confidence, (int, float)):
        return False, "Confidence must be a number"
    
    if confidence < 0 or confidence > 1:
        return False, "Confidence must be between 0 and 1"
    
    return True, "Valid confidence threshold"


def validate_camera_uid(uid: str) -> Tuple[bool, str]:
    """
    Validate camera UID format
    
    Args:
        uid: Camera UID
        
    Returns:
        Tuple of (is_valid, message)
    """
    # UID should be alphanumeric, 8-16 characters
    if not isinstance(uid, str):
        return False, "UID must be a string"
    
    if len(uid) < 8 or len(uid) > 16:
        return False, "UID must be 8-16 characters long"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', uid):
        return False, "UID can only contain letters, numbers, hyphens, and underscores"
    
    return True, "Valid camera UID"


def validate_zone_coordinates(zone: dict) -> Tuple[bool, str]:
    """
    Validate zone coordinate dictionary
    
    Args:
        zone: Zone dictionary with x_start, x_end, y_start, y_end
        
    Returns:
        Tuple of (is_valid, message)
    """
    required_keys = ['x_start', 'x_end', 'y_start', 'y_end']
    
    # Check if all keys present
    if not all(key in zone for key in required_keys):
        return False, f"Zone must contain: {', '.join(required_keys)}"
    
    # Check if values are valid
    for key in required_keys:
        value = zone[key]
        if not isinstance(value, (int, float)):
            return False, f"{key} must be a number"
        
        if value < 0 or value > 1:
            return False, f"{key} must be between 0 and 1 (ratio)"
    
    # Check if start < end
    if zone['x_start'] >= zone['x_end']:
        return False, "x_start must be less than x_end"
    
    if zone['y_start'] >= zone['y_end']:
        return False, "y_start must be less than y_end"
    
    return True, "Valid zone coordinates"


def validate_datetime_string(date_str: str) -> Tuple[bool, str]:
    """
    Validate datetime string format
    
    Args:
        date_str: Datetime string (ISO format)
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return True, "Valid datetime"
    except ValueError:
        return False, "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"


def validate_export_format(format_type: str) -> Tuple[bool, str]:
    """
    Validate export format type
    
    Args:
        format_type: Export format
        
    Returns:
        Tuple of (is_valid, message)
    """
    valid_formats = ['csv', 'json', 'excel', 'xlsx']
    
    if format_type.lower() not in valid_formats:
        return False, f"Invalid format. Allowed: {', '.join(valid_formats)}"
    
    return True, "Valid export format"


def validate_time_range(start_time: float, end_time: float) -> Tuple[bool, str]:
    """
    Validate time range
    
    Args:
        start_time: Start timestamp
        end_time: End timestamp
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not isinstance(start_time, (int, float)) or not isinstance(end_time, (int, float)):
        return False, "Times must be numbers"
    
    if start_time < 0 or end_time < 0:
        return False, "Times must be positive"
    
    if start_time >= end_time:
        return False, "Start time must be before end time"
    
    return True, "Valid time range"


def validate_alert_level(level: str) -> Tuple[bool, str]:
    """
    Validate alert level
    
    Args:
        level: Alert level
        
    Returns:
        Tuple of (is_valid, message)
    """
    valid_levels = ['info', 'warning', 'critical']
    
    if level.lower() not in valid_levels:
        return False, f"Invalid alert level. Allowed: {', '.join(valid_levels)}"
    
    return True, "Valid alert level"


def validate_behavior_type(behavior: str) -> Tuple[bool, str]:
    """
    Validate behavior type
    
    Args:
        behavior: Behavior type
        
    Returns:
        Tuple of (is_valid, message)
    """
    from core.config import BEHAVIOR_TYPES
    
    valid_behaviors = list(BEHAVIOR_TYPES.values())
    
    if behavior not in valid_behaviors:
        return False, f"Invalid behavior type. Allowed: {', '.join(valid_behaviors)}"
    
    return True, "Valid behavior type"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = Path(filename).name
    
    # Remove special characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Limit length
    if len(filename) > 200:
        name, ext = Path(filename).stem, Path(filename).suffix
        filename = name[:200-len(ext)] + ext
    
    return filename


def validate_pagination(page: int, page_size: int) -> Tuple[bool, str]:
    """
    Validate pagination parameters
    
    Args:
        page: Page number
        page_size: Items per page
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not isinstance(page, int) or not isinstance(page_size, int):
        return False, "Page and page_size must be integers"
    
    if page < 1:
        return False, "Page must be >= 1"
    
    if page_size < 1 or page_size > 1000:
        return False, "Page size must be between 1 and 1000"
    
    return True, "Valid pagination parameters"


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_or_raise(is_valid: bool, message: str):
    """
    Helper to raise ValidationError if not valid
    
    Args:
        is_valid: Validation result
        message: Error message
        
    Raises:
        ValidationError if not valid
    """
    if not is_valid:
        raise ValidationError(message)


if __name__ == "__main__":
    print("✅ Validators Module Ready")
    print("🔍 Available validators:")
    print("  - validate_video_file()")
    print("  - validate_image_file()")
    print("  - validate_confidence_threshold()")
    print("  - validate_camera_uid()")
    print("  - validate_zone_coordinates()")
    print("  - validate_export_format()")
    print("  - sanitize_filename()")