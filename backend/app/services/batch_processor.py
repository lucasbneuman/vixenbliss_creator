"""
Batch Content Processor
Orchestrates end-to-end content generation pipeline:
Template selection → LoRA generation → Hook creation → Safety check → Storage
"""

import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from app.models.avatar import Avatar
from app.models.content_piece import ContentPiece
from app.services.template_library import template_library, TemplateTier
from app.services.lora_inference import lora_inference_engine
from app.services.hook_generator import hook_generator, Platform
from app.services.content_safety import content_safety_service, SafetyRating
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


class BatchProcessorConfig:
    """Configuration for batch processing"""

    def __init__(
        self,
        num_pieces: int = 50,
        platform: Platform = Platform.INSTAGRAM,
        tier_distribution: Optional[Dict[str, float]] = None,
        include_hooks: bool = True,
        safety_check: bool = True,
        upload_to_storage: bool = True,
        generation_config: Optional[Dict[str, Any]] = None
    ):
        self.num_pieces = num_pieces
        self.platform = platform
        self.tier_distribution = tier_distribution or {
            "capa1_ratio": 0.6,  # 60% safe content
            "capa2_ratio": 0.3,  # 30% suggestive
            "capa3_ratio": 0.1   # 10% explicit
        }
        self.include_hooks = include_hooks
        self.safety_check = safety_check
        self.upload_to_storage = upload_to_storage
        self.generation_config = generation_config or {}


class BatchProcessor:
    """Service for orchestrating batch content generation"""

    def __init__(self):
        self.template_lib = template_library
        self.inference_engine = lora_inference_engine
        self.hook_gen = hook_generator
        self.safety_service = content_safety_service
        self.storage = storage_service

    async def process_batch(
        self,
        db: Session,
        avatar: Avatar,
        config: BatchProcessorConfig
    ) -> Dict[str, Any]:
        """
        Process complete batch of content

        Args:
            db: Database session
            avatar: Avatar to generate content for
            config: Batch processing configuration

        Returns:
            Processing results with generated content, statistics, costs
        """

        logger.info(f"Starting batch processing for avatar {avatar.id}")

        # Step 1: Select templates
        templates = self._select_templates(avatar, config)
        logger.info(f"Selected {len(templates)} templates")

        # Step 2: Generate images with LoRA
        content_pieces = await self._generate_images(avatar, templates, config)
        logger.info(f"Generated {len(content_pieces)} images")

        # Step 3: Generate hooks (if enabled)
        if config.include_hooks:
            content_pieces = await self._generate_hooks(avatar, content_pieces, config)
            logger.info(f"Generated hooks for {len(content_pieces)} pieces")

        # Step 4: Safety check (if enabled)
        if config.safety_check:
            content_pieces = await self._safety_check(content_pieces)
            logger.info(f"Safety check passed for {len(content_pieces)} pieces")

        # Step 5: Upload to storage (if enabled)
        if config.upload_to_storage:
            content_pieces = await self._upload_to_storage(avatar, content_pieces)
            logger.info(f"Uploaded {len(content_pieces)} pieces to storage")

        # Step 6: Save to database
        saved_pieces = self._save_to_database(db, content_pieces)
        logger.info(f"Saved {len(saved_pieces)} pieces to database")

        # Step 7: Calculate statistics
        stats = self._calculate_statistics(saved_pieces, config)

        return {
            "success": True,
            "avatar_id": str(avatar.id),
            "total_pieces": len(saved_pieces),
            "content_pieces": [self._serialize_content_piece(p) for p in saved_pieces],
            "statistics": stats,
            "config": {
                "num_pieces": config.num_pieces,
                "platform": config.platform.value,
                "tier_distribution": config.tier_distribution
            }
        }

    def _select_templates(
        self,
        avatar: Avatar,
        config: BatchProcessorConfig
    ) -> List[Dict[str, Any]]:
        """Select templates based on avatar niche and tier distribution"""

        # Get templates optimized for avatar's niche
        niche = avatar.niche or "lifestyle"

        # Get tier-distributed templates
        templates = self.template_lib.get_tier_distribution(
            count=config.num_pieces,
            **config.tier_distribution
        )

        # Filter by niche preference
        niche_templates = self.template_lib.get_templates_for_avatar(
            avatar_niche=niche,
            count=config.num_pieces
        )

        # Merge: prioritize niche templates but maintain tier distribution
        final_templates = []
        tier_counts = {"capa1": 0, "capa2": 0, "capa3": 0}

        for template in templates:
            tier = template["tier"]
            # Try to find matching niche template for this tier
            niche_match = next(
                (t for t in niche_templates if t["tier"] == tier and t not in final_templates),
                template
            )
            final_templates.append(niche_match)
            tier_counts[tier] += 1

        return final_templates[:config.num_pieces]

    async def _generate_images(
        self,
        avatar: Avatar,
        templates: List[Dict[str, Any]],
        config: BatchProcessorConfig
    ) -> List[Dict[str, Any]]:
        """Generate images using LoRA inference"""

        # Build prompts from templates
        prompts = []
        for template in templates:
            # Extract template details
            base_prompt = template["prompt_template"]
            lighting = template.get("lighting", "natural lighting")
            angle = template.get("angle", "medium shot")
            pose = template.get("pose_description", "confident pose")

            # Combine into full prompt
            full_prompt = f"{base_prompt}, {lighting}, {angle}, {pose}"
            prompts.append(full_prompt)

        # Generate images in batch
        content_pieces = await self.inference_engine.batch_generate_images(
            db=None,  # We'll save later
            avatar=avatar,
            prompts=prompts,
            batch_config=config.generation_config
        )

        # Add template metadata to content pieces
        for piece, template in zip(content_pieces, templates):
            piece.metadata = piece.metadata or {}
            piece.metadata["template"] = {
                "id": template["id"],
                "category": template["category"],
                "tier": template["tier"],
                "tags": template.get("tags", [])
            }
            piece.access_tier = template["tier"]  # Set tier from template

        return [
            {
                "content_piece": piece,
                "template": template,
                "prompt": prompt
            }
            for piece, template, prompt in zip(content_pieces, templates, prompts)
        ]

    async def _generate_hooks(
        self,
        avatar: Avatar,
        content_pieces: List[Dict[str, Any]],
        config: BatchProcessorConfig
    ) -> List[Dict[str, Any]]:
        """Generate social media hooks for content"""

        # Get avatar personality
        personality = avatar.metadata.get("personality", {})

        # Generate hooks for each piece
        for item in content_pieces:
            template = item["template"]
            piece = item["content_piece"]

            try:
                # Generate 5 hook variations
                hooks = await self.hook_gen.generate_hooks(
                    avatar_personality=personality,
                    content_type=template["category"],
                    platform=config.platform,
                    template_info=template,
                    num_variations=5
                )

                # Store best hook in content piece
                if hooks:
                    best_hook = hooks[0]  # First hook is usually best
                    piece.hook_text = best_hook["text"]

                    # Store all variations in metadata
                    piece.metadata["hooks"] = {
                        "selected": best_hook["text"],
                        "variations": [h["text"] for h in hooks],
                        "platform": config.platform.value
                    }

            except Exception as e:
                logger.warning(f"Hook generation failed for piece: {str(e)}")
                piece.hook_text = None

        return content_pieces

    async def _safety_check(
        self,
        content_pieces: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check content safety and filter rejected pieces"""

        # Prepare items for batch safety check
        items = [
            {
                "image_url": item["content_piece"].url,
                "prompt": item["prompt"]
            }
            for item in content_pieces
        ]

        # Run batch safety check
        safety_results = await self.safety_service.batch_check_safety(items)

        # Filter and update content pieces
        safe_pieces = []

        for item, safety in zip(content_pieces, safety_results):
            piece = item["content_piece"]

            # Skip rejected content
            if safety["rating"] == SafetyRating.REJECTED:
                logger.warning(f"Content rejected by safety check: {safety.get('reason', 'Unknown')}")
                continue

            # Update piece with safety info
            piece.safety_rating = safety["rating"]
            piece.metadata["safety"] = {
                "rating": safety["rating"],
                "scores": safety.get("scores", {}),
                "flagged_categories": safety.get("flagged_categories", [])
            }

            # Override tier if safety check suggests different tier
            if safety.get("access_tier"):
                piece.access_tier = safety["access_tier"]

            safe_pieces.append(item)

        return safe_pieces

    async def _upload_to_storage(
        self,
        avatar: Avatar,
        content_pieces: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Upload images to R2 storage and update URLs"""

        import httpx

        async with httpx.AsyncClient() as client:
            for idx, item in enumerate(content_pieces):
                piece = item["content_piece"]

                try:
                    # Download image from Replicate
                    response = await client.get(piece.url, timeout=30.0)
                    response.raise_for_status()
                    image_content = response.content

                    # Generate R2 path
                    file_path = f"content/{avatar.id}/{piece.id}.jpg"

                    # Upload to R2
                    upload_result = self.storage.upload_file(
                        file_content=image_content,
                        file_path=file_path,
                        content_type="image/jpeg",
                        metadata={
                            "avatar_id": str(avatar.id),
                            "content_id": str(piece.id),
                            "tier": piece.access_tier,
                            "template_id": item["template"]["id"]
                        }
                    )

                    # Update piece with R2 URL
                    piece.url = upload_result["r2_url"]

                    # Store original Replicate URL in metadata
                    piece.metadata["original_url"] = piece.url

                    logger.info(f"Uploaded piece {idx + 1}/{len(content_pieces)} to R2")

                except Exception as e:
                    logger.error(f"Upload failed for piece {idx}: {str(e)}")
                    # Keep original URL on failure

        return content_pieces

    def _save_to_database(
        self,
        db: Session,
        content_pieces: List[Dict[str, Any]]
    ) -> List[ContentPiece]:
        """Save content pieces to database"""

        saved_pieces = []

        for item in content_pieces:
            piece = item["content_piece"]

            try:
                db.add(piece)
                db.commit()
                db.refresh(piece)
                saved_pieces.append(piece)

            except Exception as e:
                logger.error(f"Database save failed: {str(e)}")
                db.rollback()

        return saved_pieces

    def _calculate_statistics(
        self,
        content_pieces: List[ContentPiece],
        config: BatchProcessorConfig
    ) -> Dict[str, Any]:
        """Calculate batch processing statistics"""

        # Tier distribution
        tier_counts = {"capa1": 0, "capa2": 0, "capa3": 0}
        for piece in content_pieces:
            tier_counts[piece.access_tier] = tier_counts.get(piece.access_tier, 0) + 1

        # Safety rating distribution
        safety_counts = {}
        for piece in content_pieces:
            rating = piece.safety_rating or "unknown"
            safety_counts[rating] = safety_counts.get(rating, 0) + 1

        # Cost estimation
        total_cost = self._estimate_total_cost(content_pieces, config)

        # Processing time (from metadata)
        total_gen_time = sum(
            piece.metadata.get("generation_time", 0)
            for piece in content_pieces
        )

        return {
            "total_pieces": len(content_pieces),
            "tier_distribution": tier_counts,
            "safety_distribution": safety_counts,
            "total_cost_usd": total_cost,
            "total_generation_time_seconds": total_gen_time,
            "average_generation_time_seconds": total_gen_time / len(content_pieces) if content_pieces else 0,
            "with_hooks": sum(1 for p in content_pieces if p.hook_text),
            "uploaded_to_storage": sum(1 for p in content_pieces if "r2_url" in str(p.url))
        }

    def _estimate_total_cost(
        self,
        content_pieces: List[ContentPiece],
        config: BatchProcessorConfig
    ) -> float:
        """Estimate total cost for batch processing"""

        num_pieces = len(content_pieces)

        # Image generation cost
        image_cost = num_pieces * 0.01  # $0.01 per image

        # Hook generation cost (if enabled)
        hook_cost = 0
        if config.include_hooks:
            hook_cost = self.hook_gen.estimate_hook_cost(num_pieces)

        # Safety check cost (if enabled)
        safety_cost = 0
        if config.safety_check:
            safety_cost = self.safety_service.estimate_safety_check_cost(num_pieces)

        # Storage cost (negligible for R2)
        storage_cost = 0.001 * num_pieces  # $0.001 per upload

        return image_cost + hook_cost + safety_cost + storage_cost

    def _serialize_content_piece(self, piece: ContentPiece) -> Dict[str, Any]:
        """Serialize content piece for API response"""

        return {
            "id": str(piece.id),
            "avatar_id": str(piece.avatar_id),
            "content_type": piece.content_type,
            "access_tier": piece.access_tier,
            "url": piece.url,
            "hook_text": piece.hook_text,
            "safety_rating": piece.safety_rating,
            "created_at": piece.created_at.isoformat() if piece.created_at else None,
            "metadata": piece.metadata
        }


# Singleton instance
batch_processor = BatchProcessor()
