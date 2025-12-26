"""
Identity Service
Handles avatar creation, facial generation, and identity component management
"""

import asyncio
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional

from app.models.avatar import Avatar
from app.models.identity_component import IdentityComponent
from app.schemas.identity import (
    AvatarCreateRequest,
    FacialGenerationRequest,
    FacialGenerationResponse,
    AvatarResponse
)
from app.services.ai_providers import ai_provider_service
from app.services.storage import storage_service


class IdentityService:
    """Service for identity generation and management"""

    async def create_avatar_with_face(
        self,
        db: Session,
        user_id: UUID,
        request: AvatarCreateRequest
    ) -> FacialGenerationResponse:
        """
        Create a new avatar with facial generation

        Workflow:
        1. Generate face using AI providers
        2. Upload image to R2 storage
        3. Create avatar record in database
        4. Return generation response
        """

        # Step 1: Generate facial image
        temp_image_url, metadata, cost, provider = await ai_provider_service.generate_with_routing(
            request.facial_generation
        )

        # Step 2: Download and upload to R2
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(temp_image_url)
                response.raise_for_status()
                image_bytes = response.content

            # Upload to R2
            file_key = f"avatars/base/{user_id}/{request.name.replace(' ', '_').lower()}_base.jpg"
            permanent_url = await storage_service.upload_file_async(
                file_data=image_bytes,
                file_key=file_key,
                content_type="image/jpeg"
            )

        except Exception as e:
            raise Exception(f"Failed to upload image to storage: {str(e)}")

        # Step 3: Create avatar in database
        avatar = Avatar(
            user_id=user_id,
            name=request.name,
            stage="face_generated",
            base_image_url=permanent_url,
            niche=request.niche,
            aesthetic_style=request.aesthetic_style,
            metadata={
                "facial_metadata": metadata.model_dump(),
                "generation_cost_usd": cost,
                "provider_used": provider,
                "generation_timestamp": str(asyncio.get_event_loop().time())
            }
        )

        db.add(avatar)
        db.commit()
        db.refresh(avatar)

        # Step 4: Create identity component for facial metadata
        identity_comp = IdentityComponent(
            avatar_id=avatar.id,
            component_type="facial_features",
            content=metadata.model_dump(),
            metadata={"provider": provider, "cost_usd": cost}
        )

        db.add(identity_comp)
        db.commit()

        # Step 5: Return response
        return FacialGenerationResponse(
            success=True,
            avatar_id=avatar.id,
            image_url=permanent_url,
            metadata=metadata,
            cost_usd=cost,
            generation_time_seconds=metadata.generation_params.get("generation_time", 0),
            provider=provider
        )

    async def generate_face_only(
        self,
        request: FacialGenerationRequest
    ) -> FacialGenerationResponse:
        """
        Generate facial image without creating avatar
        (for testing/preview purposes)
        """

        image_url, metadata, cost, provider = await ai_provider_service.generate_with_routing(
            request
        )

        return FacialGenerationResponse(
            success=True,
            avatar_id=None,
            image_url=image_url,
            metadata=metadata,
            cost_usd=cost,
            generation_time_seconds=0,
            provider=provider
        )

    def get_avatar(self, db: Session, avatar_id: UUID) -> Optional[Avatar]:
        """Retrieve avatar by ID"""
        return db.query(Avatar).filter(Avatar.id == avatar_id).first()

    def get_user_avatars(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Avatar]:
        """Get all avatars for a user"""
        return db.query(Avatar)\
            .filter(Avatar.user_id == user_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def update_avatar_stage(
        self,
        db: Session,
        avatar_id: UUID,
        new_stage: str
    ) -> Avatar:
        """Update avatar stage"""
        avatar = self.get_avatar(db, avatar_id)
        if not avatar:
            raise ValueError(f"Avatar {avatar_id} not found")

        avatar.stage = new_stage
        db.commit()
        db.refresh(avatar)

        return avatar


# Singleton instance
identity_service = IdentityService()
