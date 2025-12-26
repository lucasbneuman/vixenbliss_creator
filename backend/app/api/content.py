"""
Content Generation API Endpoints
Endpoints for content production system
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
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
from app.services.template_library import template_library, TemplateCategory, TemplateTier
from app.services.hook_generator import hook_generator, Platform
from app.services.content_safety import content_safety_service
from app.services.batch_processor import batch_processor, BatchProcessorConfig
from app.workers.tasks import generate_content_batch


router = APIRouter(
    prefix="/api/v1/content",
    tags=["Content Generation"]
)


@router.post("/generate", response_model=ContentPieceResponse)
async def generate_single_content(
    request: ContentGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate single content piece with LoRA

    E03-001: LoRA inference endpoint
    """

    # Get avatar
    avatar = db.query(Avatar).filter(Avatar.id == UUID(request.avatar_id)).first()
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
        result = await lora_inference_engine.generate_with_template(
            avatar=avatar,
            template=template
        )
    elif request.custom_prompt:
        # Generate with custom prompt
        result = await lora_inference_engine.generate_image_with_lora(
            avatar=avatar,
            prompt=request.custom_prompt
        )
    else:
        raise HTTPException(status_code=400, detail="Either template_id or custom_prompt required")

    # Create content piece
    content_piece = ContentPiece(
        avatar_id=avatar.id,
        content_type="image",
        access_tier=request.tier or "capa1",
        url=result["image_url"],
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

    # Get avatar
    avatar = db.query(Avatar).filter(Avatar.id == UUID(request.avatar_id)).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    if not avatar.lora_weights_url:
        raise HTTPException(status_code=400, detail="Avatar has no trained LoRA weights")

    # Trigger async batch generation task
    task = generate_content_batch.delay(
        avatar_id=request.avatar_id,
        num_pieces=request.num_pieces,
        platform=request.platform,
        tier_distribution=request.tier_distribution,
        include_hooks=request.include_hooks,
        safety_check=request.safety_check,
        upload_to_storage=request.upload_to_storage
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

    # Get avatar
    avatar = db.query(Avatar).filter(Avatar.id == UUID(request.avatar_id)).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    if not avatar.lora_weights_url:
        raise HTTPException(status_code=400, detail="Avatar has no trained LoRA weights")

    # Create config
    config = BatchProcessorConfig(
        num_pieces=request.num_pieces,
        platform=Platform(request.platform),
        tier_distribution=request.tier_distribution,
        include_hooks=request.include_hooks,
        safety_check=request.safety_check,
        upload_to_storage=request.upload_to_storage
    )

    # Process batch
    result = await batch_processor.process_batch(
        db=db,
        avatar=avatar,
        config=config
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
        # Get templates optimized for avatar's niche
        avatar = db.query(Avatar).filter(Avatar.id == UUID(avatar_id)).first()
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

    # Get avatar
    avatar = db.query(Avatar).filter(Avatar.id == UUID(request.avatar_id)).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    # Get personality
    personality = avatar.metadata.get("personality", {})

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

    # Get avatar
    avatar = db.query(Avatar).filter(Avatar.id == UUID(avatar_id)).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    # Get content pieces
    content_pieces = db.query(ContentPiece).filter(
        ContentPiece.id.in_([UUID(cid) for cid in content_ids])
    ).all()

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

    query = db.query(ContentPiece).filter(ContentPiece.avatar_id == UUID(avatar_id))

    if tier:
        query = query.filter(ContentPiece.access_tier == tier)

    content_pieces = query.order_by(ContentPiece.created_at.desc()).offset(offset).limit(limit).all()

    return content_pieces


@router.get("/stats/{avatar_id}")
async def get_content_stats(
    avatar_id: str,
    db: Session = Depends(get_db)
):
    """
    Get content generation statistics for avatar
    """

    avatar = db.query(Avatar).filter(Avatar.id == UUID(avatar_id)).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    # Count by tier
    content_count = db.query(ContentPiece).filter(ContentPiece.avatar_id == UUID(avatar_id)).count()

    tier_counts = {}
    for tier in ["capa1", "capa2", "capa3"]:
        count = db.query(ContentPiece).filter(
            ContentPiece.avatar_id == UUID(avatar_id),
            ContentPiece.access_tier == tier
        ).count()
        tier_counts[tier] = count

    # Safety rating distribution
    safety_counts = {}
    for rating in ["safe", "suggestive", "borderline"]:
        count = db.query(ContentPiece).filter(
            ContentPiece.avatar_id == UUID(avatar_id),
            ContentPiece.safety_rating == rating
        ).count()
        safety_counts[rating] = count

    return {
        "avatar_id": avatar_id,
        "total_content": content_count,
        "tier_distribution": tier_counts,
        "safety_distribution": safety_counts,
        "has_lora_weights": bool(avatar.lora_weights_url)
    }
