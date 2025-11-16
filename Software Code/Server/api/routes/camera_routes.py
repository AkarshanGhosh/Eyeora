# api/routes/camera_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Any
from db.connection import get_db
from api.repositories import CameraRepository
from schemas.camera import CameraCreate, CameraUpdate, CameraPublic
from security.deps.require_admin import require_admin

router = APIRouter(prefix="/cameras", tags=["cameras"])
print("📷 Camera routes loaded")

@router.post("/", response_model=CameraPublic, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_in: CameraCreate,
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """Create new camera (Admin only)"""
    repo = CameraRepository(db)
    
    # Check if UID already exists
    existing = await repo.get_by_uid(camera_in.uid)
    if existing:
        raise HTTPException(status_code=409, detail="Camera UID already exists")
    
    # Create camera
    created = await repo.create_camera(
        uid=camera_in.uid,
        name=camera_in.name,
        image_url=str(camera_in.image_url) if camera_in.image_url else None,
        location=camera_in.location,
        description=camera_in.description,
        is_active=camera_in.is_active,
        created_by=admin["id"]
    )
    
    return CameraPublic(**created)

@router.get("/", response_model=List[CameraPublic])
async def list_cameras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """List all cameras (Admin only)"""
    repo = CameraRepository(db)
    cameras = await repo.get_all(skip=skip, limit=limit)
    return [CameraPublic(**cam) for cam in cameras]

@router.get("/{uid}", response_model=CameraPublic)
async def get_camera(
    uid: str,
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """Get camera by UID (Admin only)"""
    repo = CameraRepository(db)
    camera = await repo.get_by_uid(uid)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return CameraPublic(**camera)

@router.put("/{uid}", response_model=CameraPublic)
async def update_camera(
    uid: str,
    camera_update: CameraUpdate,
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> Any:
    """Update camera (Admin only)"""
    repo = CameraRepository(db)
    
    # Check if camera exists
    existing = await repo.get_by_uid(uid)
    if not existing:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Prepare update data (exclude None values)
    update_data = camera_update.model_dump(exclude_unset=True)
    if "image_url" in update_data and update_data["image_url"]:
        update_data["image_url"] = str(update_data["image_url"])
    
    # Update camera
    success = await repo.update_camera(uid, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Update failed")
    
    # Return updated camera
    updated = await repo.get_by_uid(uid)
    return CameraPublic(**updated)

@router.delete("/{uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    uid: str,
    db=Depends(get_db),
    admin=Depends(require_admin)
) -> None:
    """Delete camera (Admin only)"""
    repo = CameraRepository(db)
    
    # Check if camera exists
    existing = await repo.get_by_uid(uid)
    if not existing:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Delete camera
    success = await repo.delete_camera(uid)
    if not success:
        raise HTTPException(status_code=500, detail="Delete failed")