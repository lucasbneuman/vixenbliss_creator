"""
Video API Endpoints
Video generation, voice synthesis, and distribution (ÉPICA 08)
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.services.video_generation import video_generation_service
from app.services.voice_synthesis import voice_synthesis_service
from app.services.storage import storage_service
from app.services.cost_tracking import cost_tracking_service
from app.models.content_piece import ContentPiece
from app.models.avatar import Avatar

import logging
import base64

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/video",
    tags=["Video Generation"]
)


# E08-001: Video Generation API

@router.post("/generate")
async def generate_video(
    avatar_id: str,
    prompt: str,
    duration: int = 4,
    aspect_ratio: str = "16:9",
    style: Optional[str] = None,
    image_url: Optional[str] = None,
    provider: Optional[str] = None,
    enable_fallback: bool = True,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Generate video using multi-provider system

    E08-001: Video generation API integration
    E08-003: Multi-provider fallback system
    """

    try:
        logger.info(f"Video generation request for avatar {avatar_id}: '{prompt[:50]}...'")

        # Verify avatar exists
        avatar = db.query(Avatar).filter(Avatar.id == UUID(avatar_id)).first()

        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar not found")

        # Generate video
        result = await video_generation_service.generate_video(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            style=style,
            image_url=image_url,
            provider=provider,
            enable_fallback=enable_fallback
        )

        video_url = result["video_url"]
        provider_used = result["provider"]
        cost = result["cost"]
        fallback_count = result.get("fallback_count", 0)

        # Upload video to R2 storage
        # Download video from provider URL first
        import httpx

        async with httpx.AsyncClient(timeout=300.0) as client:
            if video_url.startswith("data:"):
                header, data = video_url.split(",", 1)
                video_data = base64.b64decode(data)
            else:
                video_response = await client.get(video_url)
                video_response.raise_for_status()
                video_data = video_response.content

        # Upload to R2
        r2_url = await storage_service.upload_content_piece(
            avatar_id=UUID(avatar_id),
            content_data=video_data,
            content_type="video",
            tier="capa1"
        )

        # Create content piece record
        content_piece = ContentPiece(
            avatar_id=UUID(avatar_id),
            content_type="video",
            access_tier="capa1",
            url=r2_url,
            metadata={
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "style": style,
                "provider": provider_used,
                "fallback_count": fallback_count,
                "generation_params": result.get("metadata", {})
            },
            safety_rating="safe"
        )

        db.add(content_piece)
        db.commit()
        db.refresh(content_piece)

        # Track cost (E08-005)
        cost_tracking_service.track_generation_cost(
            db=db,
            avatar_id=UUID(avatar_id),
            operation_type="video",
            provider=provider_used,
            cost=cost,
            metadata={
                "duration": duration,
                "fallback_count": fallback_count
            }
        )

        logger.info(f"Video generated successfully: {r2_url} (cost: ${cost:.4f}, provider: {provider_used})")

        return {
            "success": True,
            "content_piece_id": str(content_piece.id),
            "video_url": r2_url,
            "provider": provider_used,
            "duration": duration,
            "cost": cost,
            "fallback_count": fallback_count,
            "created_at": content_piece.created_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to generate video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# E08-002: Voice Synthesis Integration

@router.post("/voice/generate")
async def generate_voice(
    avatar_id: str,
    text: str,
    voice_id: Optional[str] = None,
    language: str = "en",
    provider: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Generate voice/TTS audio

    E08-002: Voice synthesis integration
    """

    try:
        logger.info(f"Voice generation request for avatar {avatar_id}: '{text[:50]}...'")

        # Verify avatar exists
        avatar = db.query(Avatar).filter(Avatar.id == UUID(avatar_id)).first()

        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar not found")

        # Generate voice
        result = await voice_synthesis_service.generate_voice(
            text=text,
            voice_id=voice_id,
            language=language,
            provider=provider
        )

        audio_base64 = result["audio_data"]
        provider_used = result["provider"]
        cost = result["cost"]
        audio_format = result["audio_format"]

        # Decode base64 audio
        audio_data = base64.b64decode(audio_base64)

        # Upload to R2 storage
        r2_url = await storage_service.upload_content_piece(
            avatar_id=UUID(avatar_id),
            content_data=audio_data,
            content_type="audio",
            tier="capa1"
        )

        # Track cost (E08-005)
        cost_tracking_service.track_generation_cost(
            db=db,
            avatar_id=UUID(avatar_id),
            operation_type="voice",
            provider=provider_used,
            cost=cost,
            metadata={
                "char_count": result["char_count"],
                "language": language
            }
        )

        logger.info(f"Voice generated successfully: {r2_url} (cost: ${cost:.4f}, provider: {provider_used})")

        return {
            "success": True,
            "audio_url": r2_url,
            "provider": provider_used,
            "audio_format": audio_format,
            "char_count": result["char_count"],
            "cost": cost,
            "voice_id": result["voice_id"],
            "language": language
        }

    except Exception as e:
        logger.error(f"Failed to generate voice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# E08-004: Distribution Integration

@router.post("/distribution/schedule")
async def schedule_video_distribution(
    content_piece_id: str,
    platforms: list[str],
    scheduled_time: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Schedule video for distribution to social platforms

    E08-004: Distribution integration
    """

    try:
        content_piece = db.query(ContentPiece).filter(
            ContentPiece.id == UUID(content_piece_id)
        ).first()

        if not content_piece:
            raise HTTPException(status_code=404, detail="Content piece not found")

        if content_piece.content_type != "video":
            raise HTTPException(status_code=400, detail="Content piece is not a video")

        # Validate platforms
        supported_platforms = ["instagram_reels", "tiktok", "youtube_shorts"]

        for platform in platforms:
            if platform not in supported_platforms:
                raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

        # Parse scheduled time
        if scheduled_time:
            scheduled_dt = datetime.fromisoformat(scheduled_time)
        else:
            scheduled_dt = None

        # Get video metadata
        video_metadata = content_piece.metadata
        aspect_ratio = video_metadata.get("aspect_ratio", "16:9")
        duration = video_metadata.get("duration", 4)

        # Platform-specific optimization metadata
        platform_metadata = {
            "instagram_reels": {
                "recommended_aspect_ratio": "9:16",
                "max_duration": 90,
                "format": "mp4",
                "caption_limit": 2200
            },
            "tiktok": {
                "recommended_aspect_ratio": "9:16",
                "max_duration": 60,
                "format": "mp4",
                "caption_limit": 150
            },
            "youtube_shorts": {
                "recommended_aspect_ratio": "9:16",
                "max_duration": 60,
                "format": "mp4",
                "caption_limit": 100
            }
        }

        # Check if video meets platform requirements
        warnings = []

        for platform in platforms:
            platform_spec = platform_metadata[platform]

            if duration > platform_spec["max_duration"]:
                warnings.append(f"{platform}: Video duration ({duration}s) exceeds max ({platform_spec['max_duration']}s)")

            if aspect_ratio != platform_spec["recommended_aspect_ratio"]:
                warnings.append(f"{platform}: Aspect ratio ({aspect_ratio}) not optimal (recommended: {platform_spec['recommended_aspect_ratio']})")

        # Update content piece metadata with distribution schedule
        if "distribution_schedule" not in content_piece.metadata:
            content_piece.metadata["distribution_schedule"] = []

        schedule_entry = {
            "platforms": platforms,
            "scheduled_time": scheduled_dt.isoformat() if scheduled_dt else None,
            "created_at": datetime.utcnow().isoformat(),
            "status": "scheduled"
        }

        content_piece.metadata["distribution_schedule"].append(schedule_entry)

        db.commit()

        logger.info(f"Video distribution scheduled for content piece {content_piece_id} to {platforms}")

        return {
            "success": True,
            "content_piece_id": str(content_piece.id),
            "platforms": platforms,
            "scheduled_time": scheduled_dt.isoformat() if scheduled_dt else "immediate",
            "platform_metadata": platform_metadata,
            "warnings": warnings
        }

    except Exception as e:
        logger.error(f"Failed to schedule video distribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# E08-005: Video Cost Tracking

@router.get("/costs/{avatar_id}")
async def get_video_costs(
    avatar_id: str,
    db: Session = Depends(get_db)
):
    """
    Get video generation cost statistics for an avatar

    E08-005: Video cost tracking
    """

    try:
        costs = cost_tracking_service.get_avatar_costs(
            db=db,
            avatar_id=UUID(avatar_id),
            operation_type="video"
        )

        return costs

    except Exception as e:
        logger.error(f"Failed to get video costs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/user/{user_id}")
async def get_user_video_costs(
    user_id: str,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get video generation costs for all avatars of a user

    E08-005: Video cost tracking with aggregation
    """

    try:
        costs = cost_tracking_service.get_user_costs(
            db=db,
            user_id=UUID(user_id),
            days_back=days_back
        )

        # Filter for video operations only
        video_cost = costs["by_operation"].get("video", {
            "total_cost": 0.0,
            "count": 0
        })

        return {
            "user_id": user_id,
            "period_days": days_back,
            "total_video_cost": round(video_cost["total_cost"], 2),
            "video_count": video_cost["count"],
            "avg_cost_per_video": round(
                video_cost["total_cost"] / video_cost["count"], 4
            ) if video_cost["count"] > 0 else 0.0,
            "by_provider": {
                k: v for k, v in costs["by_provider"].items()
                # Filter video providers only
                if k in ["runway", "pika", "luma"]
            }
        }

    except Exception as e:
        logger.error(f"Failed to get user video costs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/costs/estimate")
async def estimate_video_cost(
    provider: str,
    duration: int,
    quantity: int = 1
):
    """
    Estimate cost for video generation

    E08-005: Cost estimation
    """

    try:
        estimated_cost = cost_tracking_service.estimate_batch_cost(
            operation_type="video",
            provider=provider,
            quantity=quantity,
            metadata={"duration": duration}
        )

        return {
            "provider": provider,
            "duration": duration,
            "quantity": quantity,
            "estimated_cost": round(estimated_cost, 2),
            "cost_per_video": round(estimated_cost / quantity, 4) if quantity > 0 else 0.0
        }

    except Exception as e:
        logger.error(f"Failed to estimate video cost: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
