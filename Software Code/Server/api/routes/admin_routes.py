# api/routes/admin_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Any
from datetime import datetime
from db.connection import get_db
from api.repositories import UserRepository, CameraRepository, AnalyticsRepository
from schemas.user import UserUpdate, UserDetailPublic
from schemas.analytics import DashboardAnalytics, UserStats, CameraStats, MediaStats, SystemStats
from security.deps.require_admin import require_admin
from security.hash.get_password_hash import get_password_hash

router = APIRouter(prefix="/admin", tags=["admin"])
print("🔐 Admin routes loaded")

# ============= ANALYTICS =============

@router.get("/dashboard", response_model=DashboardAnalytics)
async def get_dashboard_analytics(
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """Get complete dashboard analytics (Admin only)"""
    analytics_repo = AnalyticsRepository(db)
    
    user_stats = await analytics_repo.get_user_stats()
    camera_stats = await analytics_repo.get_camera_stats()
    media_stats = await analytics_repo.get_media_stats()
    online_users = await analytics_repo.get_online_users_count()
    
    return DashboardAnalytics(
        user_stats=UserStats(**user_stats),
        camera_stats=CameraStats(**camera_stats),
        media_stats=MediaStats(**media_stats),
        system_stats=SystemStats(
            online_users=online_users,
            active_live_streams=0,  # TODO: implement live stream tracking
            processing_jobs=0  # TODO: implement job queue tracking
        ),
        last_updated=datetime.utcnow()
    )

@router.get("/stats/users", response_model=UserStats)
async def get_user_statistics(
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """Get detailed user statistics (Admin only)"""
    analytics_repo = AnalyticsRepository(db)
    stats = await analytics_repo.get_user_stats()
    return UserStats(**stats)

@router.get("/stats/cameras", response_model=CameraStats)
async def get_camera_statistics(
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """Get detailed camera statistics (Admin only)"""
    analytics_repo = AnalyticsRepository(db)
    stats = await analytics_repo.get_camera_stats()
    return CameraStats(**stats)

@router.get("/stats/media", response_model=MediaStats)
async def get_media_statistics(
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """Get detailed media statistics (Admin only)"""
    analytics_repo = AnalyticsRepository(db)
    stats = await analytics_repo.get_media_stats()
    return MediaStats(**stats)

# ============= USER MANAGEMENT =============

@router.get("/users", response_model=List[UserDetailPublic])
async def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """List all users with details (Admin only)"""
    user_repo = UserRepository(db)
    users = await user_repo.get_all_users(skip=skip, limit=limit)
    return [UserDetailPublic(**user) for user in users]

@router.get("/users/{user_id}", response_model=UserDetailPublic)
async def get_user_details(
    user_id: str,
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """Get specific user details (Admin only)"""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserDetailPublic(**user)

@router.put("/users/{user_id}", response_model=UserDetailPublic)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """Update user (Admin only)"""
    user_repo = UserRepository(db)
    
    # Check if user exists
    existing = await user_repo.get_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update data
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Hash password if provided
    if "password" in update_data and update_data["password"]:
        update_data["password"] = get_password_hash(update_data["password"])
    
    # Update user
    success = await user_repo.update_user(user_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Update failed")
    
    # Return updated user
    updated = await user_repo.get_by_id(user_id)
    return UserDetailPublic(**updated)

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> None:
    """Delete user (Admin only)"""
    user_repo = UserRepository(db)
    
    # Prevent admin from deleting themselves
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Check if user exists
    existing = await user_repo.get_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete user
    success = await user_repo.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Delete failed")

# ============= MEDIA MANAGEMENT =============

@router.get("/media/videos")
async def list_processed_videos(
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """List all processed videos (Admin only)"""
    analytics_repo = AnalyticsRepository(db)
    stats = await analytics_repo.get_media_stats()
    return {
        "videos": stats["processed_videos"],
        "total": stats["total_videos"]
    }

@router.get("/media/images")
async def list_processed_images(
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """List all processed images (Admin only)"""
    analytics_repo = AnalyticsRepository(db)
    stats = await analytics_repo.get_media_stats()
    return {
        "images": stats["processed_images"],
        "total": stats["total_images"]
    }

@router.delete("/media/videos/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_processed_video(
    filename: str,
    admin=Depends(require_admin)
) -> None:
    """Delete processed video (Admin only)"""
    from core.config import PROCESSED_DIR
    file_path = PROCESSED_DIR / "videos" / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    try:
        file_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.delete("/media/images/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_processed_image(
    filename: str,
    admin=Depends(require_admin)
) -> None:
    """Delete processed image (Admin only)"""
    from core.config import PROCESSED_DIR
    file_path = PROCESSED_DIR / "images" / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        file_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")