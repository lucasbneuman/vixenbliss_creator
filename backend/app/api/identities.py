"""
Identity API Endpoints
Handles avatar creation, facial generation, and identity management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.schemas.identity import (
    AvatarCreateRequest,
    FacialGenerationRequest,
    FacialGenerationResponse,
    AvatarResponse
)
from app.services.identity_service import identity_service


router = APIRouter(prefix="/api/v1/identities", tags=["identities"])


@router.post("/components/generate", response_model=FacialGenerationResponse)
async def generate_facial_components(
    request: FacialGenerationRequest
):
    """
    Generate facial image without creating avatar (preview/testing)

    Uses multi-provider routing:
    - Replicate SDXL (fast, cheap)
    - Leonardo.ai (high quality)
    - DALL-E 3 (fallback)
    """
    try:
        result = await identity_service.generate_face_only(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Face generation failed: {str(e)}"
        )


@router.post("/avatars", response_model=FacialGenerationResponse)
async def create_avatar(
    request: AvatarCreateRequest,
    user_id: UUID,  # TODO: Extract from JWT token
    db: Session = Depends(get_db)
):
    """
    Create a new avatar with facial generation

    Workflow:
    1. Generate face using AI providers
    2. Upload to R2 storage
    3. Create avatar record
    4. Initialize identity components
    """
    try:
        result = await identity_service.create_avatar_with_face(
            db=db,
            user_id=user_id,
            request=request
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Avatar creation failed: {str(e)}"
        )


@router.get("/avatars/{avatar_id}", response_model=AvatarResponse)
def get_avatar(
    avatar_id: UUID,
    db: Session = Depends(get_db)
):
    """Get avatar details by ID"""
    avatar = identity_service.get_avatar(db, avatar_id)

    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Avatar {avatar_id} not found"
        )

    return avatar


@router.get("/avatars", response_model=List[AvatarResponse])
def list_user_avatars(
    user_id: UUID,  # TODO: Extract from JWT token
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all avatars for a user"""
    avatars = identity_service.get_user_avatars(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=limit
    )

    return avatars


@router.patch("/avatars/{avatar_id}/stage")
def update_avatar_stage(
    avatar_id: UUID,
    new_stage: str,
    db: Session = Depends(get_db)
):
    """Update avatar workflow stage"""
    try:
        avatar = identity_service.update_avatar_stage(
            db=db,
            avatar_id=avatar_id,
            new_stage=new_stage
        )
        return {"success": True, "avatar_id": avatar.id, "new_stage": avatar.stage}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
