"""
Identity Service
Handles avatar creation, facial generation, and identity component management
"""

import asyncio
import json
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional

from app.models.avatar import Avatar
from app.models.identity_component import IdentityComponent
from app.models.lora_model import LoRAModel
from app.schemas.identity import (
    AvatarCreateRequest,
    AvatarCreateWithLoRARequest,
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

        # Step 2: Download/decode and upload to R2
        try:
            import httpx
            import base64

            image_bytes = None
            content_type = "image/jpeg"
            url_str = str(temp_image_url)

            if url_str.startswith("data:"):
                header, data = url_str.split(",", 1)
                if ";base64" in header:
                    content_type = header.split(";")[0].replace("data:", "") or "image/png"
                    image_bytes = base64.b64decode(data)
                else:
                    raise ValueError("Unsupported data URL format")
            elif url_str.startswith("http"):
                async with httpx.AsyncClient() as client:
                    response = await client.get(url_str)
                    response.raise_for_status()
                    image_bytes = response.content
                    content_type = response.headers.get("Content-Type", "image/jpeg")
            else:
                # Assume raw base64 without prefix
                image_bytes = base64.b64decode(url_str)
                content_type = "image/png"

            if image_bytes is None:
                raise ValueError("No image content to upload")

            # Upload to R2
            file_ext = "jpg"
            if "png" in content_type:
                file_ext = "png"
            elif "webp" in content_type:
                file_ext = "webp"

            file_key = f"avatars/base/{user_id}/{request.name.replace(' ', '_').lower()}_base.{file_ext}"
            permanent_url = await storage_service.upload_file_async(
                file_data=image_bytes,
                file_key=file_key,
                content_type=content_type
            )

        except Exception as e:
            raise Exception(f"Failed to upload image to storage: {str(e)}")

        selected_lora = None
        if request.lora_model_id:
            selected_lora = db.query(LoRAModel).filter(
                LoRAModel.id == request.lora_model_id,
                LoRAModel.user_id == user_id,
                LoRAModel.is_active.is_(True)
            ).first()
            if not selected_lora:
                raise ValueError(f"LoRA model {request.lora_model_id} not found")

        # Step 3: Create avatar in database
        avatar = Avatar(
            user_id=user_id,
            name=request.name,
            stage="face_generated",
            base_image_url=permanent_url,
            lora_model_id=selected_lora.id if selected_lora else None,
            lora_weights_url=selected_lora.lora_weights_url if selected_lora else None,
            niche=request.niche,
            aesthetic_style=request.aesthetic_style,
            meta_data={
                "facial_metadata": metadata.model_dump(),
                "generation_config": {
                    "provider": provider,
                    "model": metadata.generation_params.get("model"),
                    "prompt": request.facial_generation.model_dump()
                },
                "selected_lora_model_id": str(selected_lora.id) if selected_lora else None,
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
            content=json.dumps(metadata.model_dump()),
            meta_data={"provider": provider, "cost_usd": cost}
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

    async def create_avatar_with_pretrained_lora(
        self,
        db: Session,
        user_id: UUID,
        request: AvatarCreateWithLoRARequest
    ) -> AvatarResponse:
        """
        Create avatar with pre-trained LoRA weights (skip training)

        Workflow:
        1. Create avatar record with LoRA info
        2. Optionally create bio identity component
        3. Stage set to "lora_ready" (ready for content generation)

        This allows using LoRAs trained externally without going through
        the full dataset generation + training pipeline.
        """

        selected_lora = None
        lora_weights_url = request.lora_weights_url
        lora_model_id = request.lora_model_id

        if lora_model_id:
            selected_lora = db.query(LoRAModel).filter(
                LoRAModel.id == lora_model_id,
                LoRAModel.user_id == user_id,
                LoRAModel.is_active.is_(True)
            ).first()
            if not selected_lora:
                raise ValueError(f"LoRA model {lora_model_id} not found")
            lora_weights_url = selected_lora.lora_weights_url

        if not lora_weights_url:
            raise ValueError("lora_weights_url is required when lora_model_id is not provided")

        # Create avatar with LoRA already configured
        avatar = Avatar(
            user_id=user_id,
            name=request.name,
            stage="lora_ready",  # Skip to ready state
            base_image_url=request.base_image_url,
            lora_model_id=selected_lora.id if selected_lora else lora_model_id,
            lora_weights_url=lora_weights_url,
            niche=request.niche,
            aesthetic_style=request.aesthetic_style,
            meta_data={
                "pretrained_lora": True,
                "skipped_training": True,
                "creation_method": "with_pretrained_lora"
            }
        )

        db.add(avatar)
        db.commit()
        db.refresh(avatar)

        # If bio provided, create identity component
        if request.bio:
            identity_comp = IdentityComponent(
                avatar_id=avatar.id,
                component_type="biography",
                content=request.bio,
                meta_data={"source": "user_provided"}
            )
            db.add(identity_comp)
            db.commit()

        return AvatarResponse.model_validate(avatar)

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
