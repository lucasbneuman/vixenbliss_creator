"""
Content Generation API Endpoints
Endpoints for content production system
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Dict, Any
from uuid import UUID

from app.database import get_db
from app.models.avatar import Avatar
from app.models.content_piece import ContentPiece
from app.schemas.content import (
    ContentGenerationRequest,
    BatchGenerationRequest,
    HookGenerationRequest,
    SafetyCheckRequest,
    TemplateListResponse,
    ContentPieceResponse,
    BatchGenerationResponse,
    HookGenerationResponse,
    SafetyCheckResponse
)
from app.services.lora_inference import lora_inference_engine
from app.services.lora_inference_fallback import fallback_generate_image
import os
from app.services.template_library import template_library, TemplateCategory, TemplateTier
from sqlalchemy import func

try:
    from app.services.hook_generator import hook_generator, Platform
except ModuleNotFoundError:
    hook_generator = None
    Platform = None

try:
    from app.services.content_safety import content_safety_service
except ModuleNotFoundError:
    content_safety_service = None


router = APIRouter(
    prefix="/api/v1/content",
    tags=["Content Generation"]
)


def _require_hook_generator() -> None:
    if hook_generator is None or Platform is None:
        raise HTTPException(status_code=503, detail="Hook generation service is not available")


def _require_content_safety() -> None:
    if content_safety_service is None:
        raise HTTPException(status_code=503, detail="Content safety service is not available")


@router.post("/generate", response_model=ContentPieceResponse)
async def generate_single_content(
    request: ContentGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate single content piece with LoRA

    E03-001: LoRA inference endpoint
    """

    # Get avatar (SQLAlchemy 2.0 style)
    stmt = select(Avatar).where(Avatar.id == UUID(request.avatar_id))
    avatar = db.execute(stmt).scalars().first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    if not avatar.lora_weights_url:
        raise HTTPException(status_code=400, detail="Avatar has no trained LoRA weights")

    # Get template or use custom prompt
    if request.template_id:
        template = template_library.get_by_id(request.template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Generate with template
        try:
            result = await lora_inference_engine.generate_with_template(
                avatar=avatar,
                template=template
            )
        except Exception:
            # Fallback to local/simple generator if enabled
            if os.getenv("ENABLE_REPLICATE_FALLBACK", "false").lower() == "true":
                fb = await fallback_generate_image(prompt=template.get("prompt_template", ""))
                if fb:
                    result = fb
                else:
                    raise
            else:
                raise
    elif request.custom_prompt:
        # Generate with custom prompt
        try:
            result = await lora_inference_engine.generate_image_with_lora(
                avatar=avatar,
                prompt=request.custom_prompt
            )
        except Exception:
            if os.getenv("ENABLE_REPLICATE_FALLBACK", "false").lower() == "true":
                fb = await fallback_generate_image(prompt=request.custom_prompt)
                if fb:
                    result = fb
                else:
                    raise
            else:
                raise
    else:
        raise HTTPException(status_code=400, detail="Either template_id or custom_prompt required")

    # Modal can return base64 only (without persisted URL). Persist a data URL so DB
    # non-null constraints are satisfied even when storage upload is not configured.
    image_url = result.get("image_url")
    if not image_url and result.get("image_base64"):
        image_url = f"data:image/png;base64,{result['image_base64']}"

    if not image_url:
        raise HTTPException(status_code=502, detail="Generation succeeded but no image URL/base64 returned")

    # Create content piece
    content_piece = ContentPiece(
        avatar_id=avatar.id,
        content_type="image",
        access_tier=request.tier or "capa1",
        url=image_url,
        metadata={
            "generation_params": result["parameters"],
            "generation_time": result["generation_time"],
            "cost": result["cost"]
        }
    )

    db.add(content_piece)
    db.commit()
    db.refresh(content_piece)

    return content_piece


@router.post("/batch", response_model=Dict[str, Any])
async def generate_batch_content(
    request: BatchGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate batch of content (50 pieces)

    E03-005: Batch processing endpoint
    Triggers async Celery task for processing
    """

    # Get avatar (SQLAlchemy 2.0 style)
    stmt = select(Avatar).where(Avatar.id == UUID(request.avatar_id))
    avatar = db.execute(stmt).scalars().first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    if not avatar.lora_weights_url:
        raise HTTPException(status_code=400, detail="Avatar has no trained LoRA weights")

    # Import lazily so /generate can run without Celery dependency installed.
    from app.workers.tasks import generate_content_batch

    # Trigger async batch generation task
    avatar_meta = getattr(avatar, "meta_data", None) or getattr(avatar, "metadata", None) or {}
    generation_config = request.generation_config
    if not generation_config:
        generation_config = avatar_meta.get("generation_config")

    task = generate_content_batch.delay(
        avatar_id=request.avatar_id,
        num_pieces=request.num_pieces,
        platform=request.platform,
        tier_distribution=request.tier_distribution,
        include_hooks=request.include_hooks,
        safety_check=request.safety_check,
        upload_to_storage=request.upload_to_storage,
        custom_prompts=request.custom_prompts,
        custom_tiers=request.custom_tiers,
        generation_config=generation_config
    )

    return {
        "success": True,
        "message": "Batch generation started",
        "task_id": task.id,
        "avatar_id": request.avatar_id,
        "num_pieces": request.num_pieces,
        "estimated_time_minutes": (request.num_pieces * 8) / 60 / 5,  # 5 concurrent
        "estimated_cost_usd": request.num_pieces * 0.01
    }


@router.post("/batch/sync", response_model=BatchGenerationResponse)
async def generate_batch_content_sync(
    request: BatchGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate batch of content synchronously (for testing/small batches)

    E03-005: Synchronous batch processing
    """

    # Get avatar (SQLAlchemy 2.0 style)
    stmt = select(Avatar).where(Avatar.id == UUID(request.avatar_id))
    avatar = db.execute(stmt).scalars().first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    if not avatar.lora_weights_url:
        raise HTTPException(status_code=400, detail="Avatar has no trained LoRA weights")

    # Create config
    avatar_meta = getattr(avatar, "meta_data", None) or getattr(avatar, "metadata", None) or {}
    generation_config = request.generation_config
    if not generation_config:
        generation_config = avatar_meta.get("generation_config")

    from app.services.batch_processor import batch_processor, BatchProcessorConfig

    if request.include_hooks:
        _require_hook_generator()

    config = BatchProcessorConfig(
        num_pieces=request.num_pieces,
        platform=Platform(request.platform),
        tier_distribution=request.tier_distribution,
        include_hooks=request.include_hooks,
        safety_check=request.safety_check,
        upload_to_storage=request.upload_to_storage,
        generation_config=generation_config
    )

    # Process batch
    result = await batch_processor.process_batch(
        db=db,
        avatar=avatar,
        config=config,
        custom_prompts=request.custom_prompts,
        custom_tiers=request.custom_tiers
    )

    return result


@router.get("/templates", response_model=TemplateListResponse)
async def get_templates(
    category: str = None,
    tier: str = None,
    avatar_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Get content templates

    E03-002: Template library endpoint
    """

    # Get templates
    if avatar_id:
        # Get templates optimized for avatar's niche (SQLAlchemy 2.0 style)
        stmt = select(Avatar).where(Avatar.id == UUID(avatar_id))
        avatar = db.execute(stmt).scalars().first()
        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar not found")

        templates = template_library.get_templates_for_avatar(
            avatar_niche=avatar.niche or "lifestyle",
            count=50
        )
    elif category:
        # Filter by category
        try:
            cat = TemplateCategory(category)
            templates = template_library.get_by_category(cat)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    elif tier:
        # Filter by tier
        try:
            tier_enum = TemplateTier(tier)
            templates = template_library.get_by_tier(tier_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")
    else:
        # Get all templates
        templates = template_library.get_all_templates()

    # Get unique categories
    categories = list(set(t["category"] for t in templates))

    return {
        "templates": templates,
        "total": len(templates),
        "categories": categories
    }


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """
    Get specific template by ID

    E03-002: Template detail endpoint
    """

    template = template_library.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.post("/hooks", response_model=HookGenerationResponse)
async def generate_hooks(
    request: HookGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate social media hooks

    E03-003: Hook generator endpoint
    """

    # Get avatar (SQLAlchemy 2.0 style)
    stmt = select(Avatar).where(Avatar.id == UUID(request.avatar_id))
    avatar = db.execute(stmt).scalars().first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    # Get personality
    avatar_meta = getattr(avatar, "meta_data", None) or getattr(avatar, "metadata", None) or {}
    personality = avatar_meta.get("personality", {})

    _require_hook_generator()

    # Generate hooks
    try:
        platform = Platform(request.platform)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {request.platform}")

    hooks = await hook_generator.generate_hooks(
        avatar_personality=personality,
        content_type=request.content_type,
        platform=platform,
        num_variations=request.num_variations
    )

    return {
        "hooks": hooks,
        "platform": request.platform,
        "content_type": request.content_type
    }


@router.post("/safety-check", response_model=SafetyCheckResponse)
async def check_content_safety(request: SafetyCheckRequest):
    """
    Check content safety

    E03-004: Content safety endpoint
    """

    _require_content_safety()

    result = await content_safety_service.check_image_safety(
        image_url=request.image_url,
        prompt=request.prompt
    )

    return result


@router.post("/upload-batch")
async def upload_content_batch(
    avatar_id: str,
    content_ids: List[str],
    db: Session = Depends(get_db)
):
    """
    Upload batch of content to R2 storage

    E03-006: Batch upload endpoint
    """

    # Get avatar (SQLAlchemy 2.0 style)
    stmt = select(Avatar).where(Avatar.id == UUID(avatar_id))
    avatar = db.execute(stmt).scalars().first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    # Get content pieces (SQLAlchemy 2.0 style)
    stmt = select(ContentPiece).where(
        ContentPiece.id.in_([UUID(cid) for cid in content_ids])
    )
    content_pieces = db.execute(stmt).scalars().all()

    if not content_pieces:
        raise HTTPException(status_code=404, detail="No content pieces found")

    # Upload to storage (implemented in batch_processor)
    from app.services.storage import storage_service
    import httpx

    uploaded = []
    async with httpx.AsyncClient() as client:
        for piece in content_pieces:
            try:
                # Download from current URL
                response = await client.get(piece.url, timeout=30.0)
                response.raise_for_status()

                # Upload to R2
                file_path = f"content/{avatar_id}/{piece.id}.jpg"
                result = storage_service.upload_file(
                    file_content=response.content,
                    file_path=file_path,
                    content_type="image/jpeg",
                    metadata={
                        "avatar_id": str(avatar_id),
                        "content_id": str(piece.id),
                        "tier": piece.access_tier
                    }
                )

                # Update URL
                piece.url = result["r2_url"]
                db.commit()

                uploaded.append({
                    "content_id": str(piece.id),
                    "url": result["r2_url"],
                    "success": True
                })

            except Exception as e:
                uploaded.append({
                    "content_id": str(piece.id),
                    "error": str(e),
                    "success": False
                })

    return {
        "avatar_id": avatar_id,
        "total_uploaded": len([u for u in uploaded if u["success"]]),
        "total_failed": len([u for u in uploaded if not u["success"]]),
        "results": uploaded
    }


@router.get("/avatar/{avatar_id}/content", response_model=List[ContentPieceResponse])
async def get_avatar_content(
    avatar_id: str,
    tier: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get content for specific avatar

    Query with optional tier filter
    """

    # Build query (SQLAlchemy 2.0 style)
    stmt = select(ContentPiece).where(ContentPiece.avatar_id == UUID(avatar_id))

    if tier:
        stmt = stmt.where(ContentPiece.access_tier == tier)

    stmt = stmt.order_by(ContentPiece.created_at.desc()).offset(offset).limit(limit)
    content_pieces = db.execute(stmt).scalars().all()

    return content_pieces


@router.get("/stats/{avatar_id}")
async def get_content_stats(
    avatar_id: str,
    db: Session = Depends(get_db)
):
    """
    Get content generation statistics for avatar
    """

    # Get avatar (SQLAlchemy 2.0 style)
    stmt = select(Avatar).where(Avatar.id == UUID(avatar_id))
    avatar = db.execute(stmt).scalars().first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    # Count by tier (SQLAlchemy 2.0 style)
    from sqlalchemy import func
    content_count = db.execute(
        select(func.count()).select_from(ContentPiece).where(
            ContentPiece.avatar_id == UUID(avatar_id)
        )
    ).scalar()

    tier_counts = {}
    for tier in ["capa1", "capa2", "capa3"]:
        count = db.execute(
            select(func.count()).select_from(ContentPiece).where(
                ContentPiece.avatar_id == UUID(avatar_id),
                ContentPiece.access_tier == tier
            )
        ).scalar()
        tier_counts[tier] = count

    # Safety rating distribution (SQLAlchemy 2.0 style)
    safety_counts = {}
    for rating in ["safe", "suggestive", "borderline"]:
        count = db.execute(
            select(func.count()).select_from(ContentPiece).where(
                ContentPiece.avatar_id == UUID(avatar_id),
                ContentPiece.safety_rating == rating
            )
        ).scalar()
        safety_counts[rating] = count

    return {
        "avatar_id": avatar_id,
        "total_content": content_count,
        "tier_distribution": tier_counts,
        "safety_distribution": safety_counts,
        "has_lora_weights": bool(avatar.lora_weights_url)
    }


@router.get("/health")
async def system_2_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint for System 2 (Content Production)
    
    Verifies:
    - Database connectivity
    - Template library functionality
    - Provider chain availability
    - R2 storage credentials
    
    Returns:
    - status: "healthy" | "degraded" | "unhealthy"
    - checks: detailed status of each component
    - timestamp: check timestamp in ISO format
    """
    import logging
    import time
    from datetime import datetime

    logger = logging.getLogger(__name__)
    check_start = time.time()

    status = "healthy"
    checks = {}
    errors = []

    # Check 1: Database connectivity
    try:
        avatars_count = db.execute(select(func.count()).select_from(Avatar)).scalar()
        content_count = db.execute(select(func.count()).select_from(ContentPiece)).scalar()
        checks["database"] = {
            "status": "online",
            "avatars_count": avatars_count,
            "content_pieces_count": content_count
        }
        logger.debug(f"Health check: Database OK | Avatars: {avatars_count}, Content: {content_count}")
    except Exception as e:
        status = "unhealthy"
        checks["database"] = {
            "status": "offline",
            "error": str(e)[:100]
        }
        errors.append(f"Database: {str(e)[:100]}")
        logger.error(f"Health check: Database FAILED | Error: {str(e)[:100]}")

    # Check 2: Template library functionality
    try:
        all_templates = template_library.get_all_templates()
        templates_by_tier = {
            "capa1": len(template_library.get_by_tier(TemplateTier.CAPA1)),
            "capa2": len(template_library.get_by_tier(TemplateTier.CAPA2)),
            "capa3": len(template_library.get_by_tier(TemplateTier.CAPA3))
        }
        cache_stats = template_library.get_cache_stats()
        checks["template_library"] = {
            "status": "loaded",
            "total_templates": len(all_templates),
            "tier_distribution": templates_by_tier,
            "cache_performance": cache_stats
        }
        logger.debug(
            f"Health check: Template library OK | Templates: {len(all_templates)} | "
            f"Cache hits: {cache_stats['cache_hits']}"
        )
    except Exception as e:
        status = "degraded"
        checks["template_library"] = {
            "status": "error",
            "error": str(e)[:100]
        }
        errors.append(f"Template library: {str(e)[:100]}")
        logger.error(f"Health check: Template library FAILED | Error: {str(e)[:100]}")

    # Check 3: Inference engine availability
    try:
        inference_status = lora_inference_engine.get_status()
        checks["inference_engine"] = {
            "status": "available",
            "engine_type": type(lora_inference_engine).__name__,
            "details": inference_status
        }
        logger.debug(f"Health check: Inference engine OK | Type: {type(lora_inference_engine).__name__}")
    except Exception as e:
        status = "degraded"
        checks["inference_engine"] = {
            "status": "error",
            "error": str(e)[:100]
        }
        errors.append(f"Inference engine: {str(e)[:100]}")
        logger.warning(f"Health check: Inference engine FAILED | Error: {str(e)[:100]}")

    # Check 4: Hook generator availability
    try:
        if hook_generator:
            checks["hook_generator"] = {
                "status": "available",
                "engine_type": type(hook_generator).__name__
            }
            logger.debug(f"Health check: Hook generator OK | Type: {type(hook_generator).__name__}")
        else:
            checks["hook_generator"] = {
                "status": "disabled",
                "note": "Hook generator not configured"
            }
            logger.debug("Health check: Hook generator disabled")
    except Exception as e:
        status = "degraded"
        checks["hook_generator"] = {
            "status": "error",
            "error": str(e)[:100]
        }
        errors.append(f"Hook generator: {str(e)[:100]}")
        logger.warning(f"Health check: Hook generator FAILED | Error: {str(e)[:100]}")

    # Check 5: Safety service availability
    try:
        if content_safety_service:
            checks["safety_service"] = {
                "status": "available",
                "engine_type": type(content_safety_service).__name__
            }
            logger.debug(f"Health check: Safety service OK | Type: {type(content_safety_service).__name__}")
        else:
            checks["safety_service"] = {
                "status": "disabled",
                "note": "Safety service not configured"
            }
            logger.debug("Health check: Safety service disabled")
    except Exception as e:
        status = "degraded"
        checks["safety_service"] = {
            "status": "error",
            "error": str(e)[:100]
        }
        errors.append(f"Safety service: {str(e)[:100]}")
        logger.warning(f"Health check: Safety service FAILED | Error: {str(e)[:100]}")

    # Check 6: R2 storage credentials
    try:
        r2_account = os.getenv("R2_ACCOUNT_ID")
        r2_access = os.getenv("R2_ACCESS_KEY_ID")
        r2_secret = os.getenv("R2_SECRET_ACCESS_KEY")
        r2_bucket = os.getenv("R2_BUCKET_NAME")

        r2_configured = bool(r2_account and r2_access and r2_secret and r2_bucket)

        checks["r2_storage"] = {
            "status": "configured" if r2_configured else "unconfigured",
            "account_id_set": bool(r2_account),
            "access_key_set": bool(r2_access),
            "secret_key_set": bool(r2_secret),
            "bucket_name": r2_bucket or "not-set"
        }

        if r2_configured:
            logger.debug(f"Health check: R2 storage OK | Bucket: {r2_bucket}")
        else:
            status = "degraded"
            logger.warning("Health check: R2 storage NOT fully configured")

    except Exception as e:
        status = "degraded"
        checks["r2_storage"] = {
            "status": "error",
            "error": str(e)[:100]
        }
        errors.append(f"R2 storage: {str(e)[:100]}")
        logger.warning(f"Health check: R2 storage FAILED | Error: {str(e)[:100]}")

    check_duration = time.time() - check_start

    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "errors": errors,
        "duration_ms": round(check_duration * 1000, 2)
    }

