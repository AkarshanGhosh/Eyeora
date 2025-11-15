"""
Video Processing API Routes
Handles video upload, processing, and analytics
Location: Software Code/Server/routes/video_routes.py
"""

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
from pathlib import Path
from datetime import datetime
import uuid
import asyncio

from core.video_processor import VideoProcessor
from core.detection_engine import DetectionEngine
from core.config import UPLOADS_DIR, PROCESSED_DIR, DATA_DIR
from utils.validators import validate_video_file, sanitize_filename
from utils.video_utils import get_video_info

# Create router
router = APIRouter(prefix="/video", tags=["Video Processing"])

# Store processing jobs
processing_jobs = {}


# ==================== Video Upload ====================

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    generate_output: bool = Query(True, description="Generate annotated video"),
    export_csv: bool = Query(True, description="Export analytics to CSV"),
    confidence: Optional[float] = Query(None, description="Detection confidence")
):
    """
    Upload video for processing
    
    - **file**: Video file (MP4, AVI, MOV, etc.)
    - **generate_output**: Create annotated output video
    - **export_csv**: Export analytics data
    - **confidence**: Detection threshold (0-1)
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Validate and save file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = sanitize_filename(file.filename)
        filename = f"{timestamp}_{job_id[:8]}_{safe_filename}"
        
        upload_path = UPLOADS_DIR / "videos" / filename
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Validate video
        is_valid, message = validate_video_file(str(upload_path))
        if not is_valid:
            upload_path.unlink()  # Delete invalid file
            raise HTTPException(status_code=400, detail=message)
        
        # Get video info
        video_info = get_video_info(str(upload_path))
        
        # Create job entry
        processing_jobs[job_id] = {
            "status": "uploaded",
            "filename": filename,
            "upload_path": str(upload_path),
            "video_info": video_info,
            "config": {
                "generate_output": generate_output,
                "export_csv": export_csv,
                "confidence": confidence
            },
            "created_at": datetime.now().isoformat(),
            "progress": 0
        }
        
        return {
            "status": "success",
            "job_id": job_id,
            "filename": filename,
            "video_info": video_info,
            "message": "Video uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Process Video ====================

async def process_video_background(job_id: str):
    """Background task to process video"""
    try:
        job = processing_jobs[job_id]
        job["status"] = "processing"
        job["started_at"] = datetime.now().isoformat()
        
        # Initialize processor
        processor = VideoProcessor()
        
        # Process video
        output_path = None
        if job["config"]["generate_output"]:
            output_filename = f"processed_{job_id[:8]}.mp4"
            output_path = str(PROCESSED_DIR / "videos" / output_filename)
        
        result = processor.process_video(
            video_path=job["upload_path"],
            output_path=output_path,
            generate_output_video=job["config"]["generate_output"],
            export_csv=job["config"]["export_csv"]
        )
        
        # Update job with results
        job["status"] = "completed"
        job["completed_at"] = datetime.now().isoformat()
        job["result"] = {
            "total_tracks": result["total_tracks"],
            "summary": result["summary"],
            "processing_time": result["processing_time"],
            "output_video": result.get("output_video_path"),
            "csv_path": result.get("csv_path")
        }
        
    except Exception as e:
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)
        print(f"Processing failed for job {job_id}: {e}")


@router.post("/process/{job_id}")
async def process_video(job_id: str, background_tasks: BackgroundTasks):
    """
    Start processing uploaded video
    
    - **job_id**: Job ID from upload
    """
    try:
        if job_id not in processing_jobs:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        job = processing_jobs[job_id]
        
        if job["status"] != "uploaded":
            raise HTTPException(
                status_code=400,
                detail=f"Job is already {job['status']}"
            )
        
        # Add background processing task
        background_tasks.add_task(process_video_background, job_id)
        
        return {
            "status": "success",
            "job_id": job_id,
            "message": "Processing started",
            "estimated_time": job["video_info"]["duration"] * 2  # Rough estimate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Job Status ====================

@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get processing job status
    
    Returns current status and results if completed
    """
    try:
        if job_id not in processing_jobs:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        job = processing_jobs[job_id]
        
        response = {
            "job_id": job_id,
            "status": job["status"],
            "filename": job["filename"],
            "video_info": job["video_info"],
            "created_at": job["created_at"]
        }
        
        if job["status"] == "processing":
            response["started_at"] = job.get("started_at")
            response["progress"] = job.get("progress", 0)
        
        if job["status"] == "completed":
            response["completed_at"] = job.get("completed_at")
            response["result"] = job.get("result")
        
        if job["status"] == "failed":
            response["error"] = job.get("error")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Get Results ====================

@router.get("/results/{job_id}")
async def get_results(job_id: str):
    """
    Get detailed results for completed job
    """
    try:
        if job_id not in processing_jobs:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        job = processing_jobs[job_id]
        
        if job["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Job is {job['status']}, not completed"
            )
        
        result = job["result"]
        
        return {
            "status": "success",
            "job_id": job_id,
            "analytics": {
                "total_visitors": result["summary"]["total_visitors"],
                "conversion_rate": result["summary"]["conversion_rate"],
                "avg_visit_duration": result["summary"]["avg_visit_duration"],
                "purchasers": result["summary"]["purchasers"],
                "window_shoppers": result["summary"]["window_shoppers"],
                "browsers": result["summary"]["browsers"],
                "passing_through": result["summary"]["passing_through"],
                "idle": result["summary"]["idle"]
            },
            "files": {
                "output_video": f"/video/download/video/{job_id}" if result.get("output_video") else None,
                "csv": f"/video/download/csv/{job_id}" if result.get("csv_path") else None
            },
            "processing_time": result["processing_time"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Download Files ====================

@router.get("/download/video/{job_id}")
async def download_video(job_id: str):
    """Download processed video"""
    try:
        if job_id not in processing_jobs:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        job = processing_jobs[job_id]
        
        if job["status"] != "completed":
            raise HTTPException(status_code=400, detail="Job not completed")
        
        video_path = job["result"].get("output_video")
        if not video_path or not Path(video_path).exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=f"processed_{job_id[:8]}.mp4"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/csv/{job_id}")
async def download_csv(job_id: str):
    """Download CSV analytics"""
    try:
        if job_id not in processing_jobs:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        job = processing_jobs[job_id]
        
        if job["status"] != "completed":
            raise HTTPException(status_code=400, detail="Job not completed")
        
        csv_path = job["result"].get("csv_path")
        if not csv_path or not Path(csv_path).exists():
            raise HTTPException(status_code=404, detail="CSV file not found")
        
        return FileResponse(
            csv_path,
            media_type="text/csv",
            filename=f"analytics_{job_id[:8]}.csv"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== List Jobs ====================

@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum jobs to return")
):
    """
    List all processing jobs
    
    - **status**: Filter by status (uploaded, processing, completed, failed)
    - **limit**: Maximum jobs to return
    """
    try:
        jobs = []
        
        for job_id, job in processing_jobs.items():
            if status and job["status"] != status:
                continue
            
            jobs.append({
                "job_id": job_id,
                "filename": job["filename"],
                "status": job["status"],
                "created_at": job["created_at"],
                "video_duration": job["video_info"]["duration"]
            })
        
        # Sort by created_at (newest first)
        jobs.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "status": "success",
            "total_jobs": len(jobs),
            "jobs": jobs[:limit]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Delete Job ====================

@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete processing job and associated files
    """
    try:
        if job_id not in processing_jobs:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        job = processing_jobs[job_id]
        
        # Delete uploaded file
        upload_path = Path(job["upload_path"])
        if upload_path.exists():
            upload_path.unlink()
        
        # Delete processed files if completed
        if job["status"] == "completed":
            result = job["result"]
            
            if result.get("output_video"):
                output_path = Path(result["output_video"])
                if output_path.exists():
                    output_path.unlink()
            
            if result.get("csv_path"):
                csv_path = Path(result["csv_path"])
                if csv_path.exists():
                    csv_path.unlink()
        
        # Remove from jobs
        del processing_jobs[job_id]
        
        return {
            "status": "success",
            "message": f"Job {job_id} deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Health Check ====================

@router.get("/health")
async def health_check():
    """Video processing system health check"""
    status_counts = {}
    for job in processing_jobs.values():
        status = job["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "status": "healthy",
        "total_jobs": len(processing_jobs),
        "jobs_by_status": status_counts,
        "timestamp": datetime.now().isoformat()
    }