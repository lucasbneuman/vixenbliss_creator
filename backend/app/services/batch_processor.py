"""
Batch Content Processor
Orchestrates end-to-end content generation pipeline:
Template selection → LoRA generation → Hook creation → Safety check → Storage
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from app.models.avatar import Avatar
from app.models.content_piece import ContentPiece
from app.services.template_library import template_library, TemplateTier
from app.services.lora_inference import lora_inference_engine
from app.services.hook_generator import hook_generator, Platform
from app.services.prompt_enhancer import prompt_enhancer
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
        config: BatchProcessorConfig,
        custom_prompts: Optional[List[str]] = None,
        custom_tiers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process complete batch of content with granular timing

        Args:
            db: Database session
            avatar: Avatar to generate content for
            config: Batch processing configuration
            custom_prompts: Custom prompts (optional)
            custom_tiers: Custom access tiers (optional)

        Returns:
            Processing results with generated content, statistics, costs, and timing metrics
        """

        batch_start = time.time()
        total_duration = 0
        step_metrics = []

        try:
            logger.info(
                f"[BATCH START] Avatar: {avatar.id}, "
                f"Pieces: {config.num_pieces}, Platform: {config.platform.value}"
            )

            # Step 1: Select templates or use custom prompts
            step1_start = time.time()
            templates = self._select_templates(avatar, config, custom_prompts)
            step1_duration = time.time() - step1_start
            step_metrics.append({
                "step": 1,
                "name": "template_selection",
                "duration_ms": round(step1_duration * 1000, 2),
                "result_count": len(templates),
                "status": "success"
            })
            logger.info(
                f"[STEP 1/7] Template Selection | "
                f"Selected: {len(templates)} | Duration: {step1_duration:.2f}s"
            )

            # Step 2: Generate images with LoRA
            step2_start = time.time()
            content_pieces = await self._generate_images(
                avatar=avatar,
                templates=templates,
                config=config,
                custom_prompts=custom_prompts,
                custom_tiers=custom_tiers
            )
            step2_duration = time.time() - step2_start
            step_metrics.append({
                "step": 2,
                "name": "image_generation",
                "duration_ms": round(step2_duration * 1000, 2),
                "result_count": len(content_pieces),
                "status": "success"
            })
            logger.info(
                f"[STEP 2/7] Image Generation | "
                f"Generated: {len(content_pieces)} | Duration: {step2_duration:.2f}s | "
                f"Avg per image: {(step2_duration / len(content_pieces) if content_pieces else 0):.2f}s"
            )

            # Step 3: Generate hooks (if enabled)
            if config.include_hooks:
                step3_start = time.time()
                content_pieces = await self._generate_hooks(avatar, content_pieces, config)
                step3_duration = time.time() - step3_start
                with_hooks = sum(1 for p in content_pieces if p.get("content_piece").hook_text)
                step_metrics.append({
                    "step": 3,
                    "name": "hook_generation",
                    "duration_ms": round(step3_duration * 1000, 2),
                    "result_count": with_hooks,
                    "status": "success"
                })
                logger.info(
                    f"[STEP 3/7] Hook Generation | "
                    f"Generated: {with_hooks}/{len(content_pieces)} | Duration: {step3_duration:.2f}s"
                )
            else:
                logger.info("[STEP 3/7] Hook Generation | SKIPPED (disabled)")

            # Step 4: Safety check (if enabled)
            if config.safety_check:
                step4_start = time.time()
                content_pieces = await self._safety_check(content_pieces)
                step4_duration = time.time() - step4_start
                rejected = config.num_pieces - len(content_pieces)
                step_metrics.append({
                    "step": 4,
                    "name": "safety_check",
                    "duration_ms": round(step4_duration * 1000, 2),
                    "result_count": len(content_pieces),
                    "rejected_count": rejected,
                    "status": "success"
                })
                logger.info(
                    f"[STEP 4/7] Safety Check | "
                    f"Passed: {len(content_pieces)}, Rejected: {rejected} | Duration: {step4_duration:.2f}s"
                )
            else:
                logger.info("[STEP 4/7] Safety Check | SKIPPED (disabled)")

            # Step 5: Upload to storage (if enabled)
            if config.upload_to_storage:
                step5_start = time.time()
                content_pieces = await self._upload_to_storage(avatar, content_pieces)
                step5_duration = time.time() - step5_start
                uploaded = sum(1 for p in content_pieces if "r2_url" in str(p.get("content_piece").url))
                step_metrics.append({
                    "step": 5,
                    "name": "storage_upload",
                    "duration_ms": round(step5_duration * 1000, 2),
                    "result_count": uploaded,
                    "status": "success"
                })
                logger.info(
                    f"[STEP 5/7] Storage Upload | "
                    f"Uploaded: {uploaded}/{len(content_pieces)} to R2 | Duration: {step5_duration:.2f}s"
                )
            else:
                logger.info("[STEP 5/7] Storage Upload | SKIPPED (disabled)")

            # Step 6: Save to database
            step6_start = time.time()
            saved_pieces = self._save_to_database(db, content_pieces)
            step6_duration = time.time() - step6_start
            step_metrics.append({
                "step": 6,
                "name": "database_save",
                "duration_ms": round(step6_duration * 1000, 2),
                "result_count": len(saved_pieces),
                "status": "success"
            })
            logger.info(
                f"[STEP 6/7] Database Save | "
                f"Saved: {len(saved_pieces)} | Duration: {step6_duration:.2f}s"
            )

            # Step 7: Calculate statistics
            step7_start = time.time()
            stats = self._calculate_statistics(saved_pieces, config)
            step7_duration = time.time() - step7_start
            step_metrics.append({
                "step": 7,
                "name": "statistics_calculation",
                "duration_ms": round(step7_duration * 1000, 2),
                "result_count": 1,
                "status": "success"
            })
            logger.info(
                f"[STEP 7/7] Statistics Calculation | Duration: {step7_duration:.2f}s"
            )

            total_duration = time.time() - batch_start
            logger.info(
                f"[BATCH COMPLETE] Avatar: {avatar.id} | "
                f"Total Duration: {total_duration:.2f}s | "
                f"Pieces: {len(saved_pieces)} | Cost: ${stats['total_cost_usd']:.4f}"
            )

            return {
                "success": True,
                "avatar_id": str(avatar.id),
                "total_pieces": len(saved_pieces),
                "content_pieces": [self._serialize_content_piece(p) for p in saved_pieces],
                "statistics": stats,
                "timing_metrics": {
                    "batch_total_ms": round(total_duration * 1000, 2),
                    "step_timings": step_metrics
                },
                "config": {
                    "num_pieces": config.num_pieces,
                    "platform": config.platform.value,
                    "tier_distribution": config.tier_distribution
                }
            }

        except Exception as e:
            total_duration = time.time() - batch_start
            logger.error(
                f"[BATCH ERROR] Avatar: {avatar.id} | "
                f"Duration: {total_duration:.2f}s | Error: {str(e)}"
            )
            raise

    def _select_templates(
        self,
        avatar: Avatar,
        config: BatchProcessorConfig,
        custom_prompts: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Select templates based on avatar niche and tier distribution with logging"""

        if custom_prompts:
            logger.debug(
                f"Template selection | Using {len(custom_prompts)} custom prompts"
            )
            return [
                {
                    "id": "custom",
                    "category": "custom",
                    "tier": "capa1",
                    "prompt_template": prompt
                }
                for prompt in custom_prompts
            ]

        # Get templates optimized for avatar's niche
        niche = avatar.niche or "lifestyle"
        logger.debug(f"Template selection | Avatar niche: {niche}")

        # Get tier-distributed templates
        templates = self.template_lib.get_tier_distribution(
            count=config.num_pieces,
            **config.tier_distribution
        )
        logger.debug(
            f"Template selection | Tier distribution: {config.tier_distribution} | "
            f"Retrieved: {len(templates)} templates"
        )

        # Filter by niche preference
        niche_templates = self.template_lib.get_templates_for_avatar(
            avatar_niche=niche,
            count=config.num_pieces
        )
        logger.debug(
            f"Template selection | Niche-optimized: {len(niche_templates)} templates"
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

        final_templates = final_templates[:config.num_pieces]

        logger.debug(
            f"Template selection | Final tier distribution: {tier_counts} | "
            f"Total selected: {len(final_templates)}"
        )

        return final_templates

    async def _generate_images(
        self,
        avatar: Avatar,
        templates: List[Dict[str, Any]],
        config: BatchProcessorConfig,
        custom_prompts: Optional[List[str]] = None,
        custom_tiers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generate images using LoRA inference"""

        # Build prompts
        if custom_prompts:
            prompts = custom_prompts
        else:
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

        # Optional prompt enhancement (GPT-4o mini)
        if config.generation_config.get("enhance_prompts", True):
            context_items = []
            for template, prompt in zip(templates, prompts):
                context_items.append({
                    "template": {
                        "id": template.get("id"),
                        "category": template.get("category"),
                        "tier": template.get("tier"),
                        "tags": template.get("tags", [])
                    },
                    "avatar": {
                        "niche": avatar.niche,
                        "style": avatar.aesthetic_style
                    },
                    "base_prompt": prompt
                })
            prompts = await prompt_enhancer.enhance_prompts(prompts, context_items)

        # Generate images in batch
        content_pieces = await self.inference_engine.batch_generate_images(
            db=None,  # We'll save later
            avatar=avatar,
            prompts=prompts,
            batch_config=config.generation_config
        )

        # Add template metadata to content pieces
        for idx, (piece, template) in enumerate(zip(content_pieces, templates)):
            piece.metadata = piece.metadata or {}
            piece.metadata["template"] = {
                "id": template["id"],
                "category": template["category"],
                "tier": template["tier"],
                "tags": template.get("tags", [])
            }
            if custom_tiers and idx < len(custom_tiers):
                piece.access_tier = custom_tiers[idx]
            else:
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
        """Generate social media hooks for content with detailed logging"""

        # Get avatar personality
        avatar_meta = getattr(avatar, "meta_data", None) or getattr(avatar, "metadata", None) or {}
        personality = avatar_meta.get("personality", {})

        success_count = 0
        error_count = 0

        # Generate hooks for each piece
        for idx, item in enumerate(content_pieces, 1):
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
                    piece.metadata = piece.metadata or {}
                    piece.metadata["hooks"] = {
                        "selected": best_hook["text"][:100],  # Truncate for logging safety
                        "variations_count": len(hooks),
                        "platform": config.platform.value
                    }
                    success_count += 1
                    logger.debug(
                        f"Hook generation [{idx}/{len(content_pieces)}] | "
                        f"Success | Category: {template['category']} | "
                        f"Variations: {len(hooks)}"
                    )
                else:
                    error_count += 1
                    logger.warning(f"Hook generation [{idx}/{len(content_pieces)}] | No hooks generated")

            except Exception as e:
                error_count += 1
                logger.warning(
                    f"Hook generation [{idx}/{len(content_pieces)}] | "
                    f"Error: {str(e)[:100]}"
                )
                piece.hook_text = None

        logger.debug(
            f"Hook generation summary | Success: {success_count}/{len(content_pieces)} | "
            f"Errors: {error_count}"
        )

        return content_pieces

    async def _safety_check(
        self,
        content_pieces: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check content safety and filter rejected pieces with detailed logging"""

        # Prepare items for batch safety check
        items = [
            {
                "image_url": item["content_piece"].url,
                "prompt": item["prompt"]
            }
            for item in content_pieces
        ]

        logger.debug(f"Running safety check on {len(items)} items")

        # Run batch safety check
        safety_results = await self.safety_service.batch_check_safety(items)

        # Filter and update content pieces
        safe_pieces = []
        rejected_count = 0
        rating_distribution = {}

        for idx, (item, safety) in enumerate(zip(content_pieces, safety_results), 1):
            piece = item["content_piece"]

            # Track rating distribution
            rating = safety.get("rating", "unknown")
            rating_distribution[rating] = rating_distribution.get(rating, 0) + 1

            # Skip rejected content
            if safety["rating"] == SafetyRating.REJECTED:
                rejected_count += 1
                reason = safety.get("reason", "Unknown")
                logger.debug(
                    f"Content rejected [{idx}/{len(content_pieces)}] | "
                    f"Reason: {reason[:80]}"
                )
                continue

            # Update piece with safety info
            piece.safety_rating = safety["rating"]
            piece.metadata = piece.metadata or {}
            piece.metadata["safety"] = {
                "rating": safety["rating"],
                "flagged_categories": safety.get("flagged_categories", [])
            }

            # Override tier if safety check suggests different tier
            if safety.get("access_tier"):
                piece.access_tier = safety["access_tier"]
                logger.debug(
                    f"Content tier updated [{idx}/{len(content_pieces)}] | "
                    f"New tier: {safety['access_tier']} | Rating: {rating}"
                )

            safe_pieces.append(item)

        logger.debug(
            f"Safety check summary | Rating distribution: {rating_distribution} | "
            f"Rejected: {rejected_count}/{len(content_pieces)} | "
            f"Approved: {len(safe_pieces)}"
        )

        return safe_pieces

    async def _upload_to_storage(
        self,
        avatar: Avatar,
        content_pieces: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Upload images to R2 storage and update URLs with detailed logging"""

        import httpx
        import os
        import base64

        r2_public_url = os.getenv("R2_PUBLIC_URL", "").rstrip("/")
        upload_success = 0
        upload_skipped = 0
        upload_errors = 0

        async with httpx.AsyncClient() as client:
            for idx, item in enumerate(content_pieces, 1):
                piece = item["content_piece"]

                try:
                    if not piece.url:
                        upload_skipped += 1
                        logger.debug(f"Upload [{idx}/{len(content_pieces)}] | Skipped: No URL")
                        continue

                    # Skip if already stored in R2
                    if r2_public_url and str(piece.url).startswith(r2_public_url):
                        upload_skipped += 1
                        logger.debug(f"Upload [{idx}/{len(content_pieces)}] | Skipped: Already in R2")
                        continue

                    original_url = piece.url
                    image_content = None
                    content_type = "image/jpeg"

                    url_str = str(piece.url)

                    # Fetch image content
                    if url_str.startswith("data:"):
                        header, data = url_str.split(",", 1)
                        if ";base64" in header:
                            content_type = header.split(";")[0].replace("data:", "") or "image/png"
                            image_content = base64.b64decode(data)
                        else:
                            raise ValueError("Unsupported data URL format")
                    elif url_str.startswith("http"):
                        response = await client.get(url_str, timeout=30.0)
                        response.raise_for_status()
                        image_content = response.content
                        content_type = response.headers.get("Content-Type", "image/jpeg")
                    else:
                        # Assume raw base64 without prefix
                        image_content = base64.b64decode(url_str)
                        content_type = "image/png"

                    if image_content is None:
                        raise ValueError("No image content to upload")

                    # Generate R2 path
                    piece_id = piece.id
                    if not piece_id:
                        import uuid as uuid_pkg
                        piece_id = uuid_pkg.uuid4()

                    file_ext = "jpg"
                    if "png" in content_type:
                        file_ext = "png"
                    elif "webp" in content_type:
                        file_ext = "webp"

                    file_path = f"content/{avatar.id}/{piece_id}.{file_ext}"

                    # Upload to R2
                    upload_result = self.storage.upload_file(
                        file_content=image_content,
                        file_path=file_path,
                        content_type=content_type,
                        metadata={
                            "avatar_id": str(avatar.id),
                            "content_id": str(piece.id),
                            "tier": piece.access_tier,
                            "template_id": item["template"]["id"]
                        }
                    )

                    # Update piece with R2 URL
                    piece.url = upload_result["r2_url"]

                    # Store original URL in metadata
                    piece.metadata = piece.metadata or {}
                    piece.metadata["original_url"] = original_url

                    upload_success += 1
                    logger.debug(
                        f"Upload [{idx}/{len(content_pieces)}] | Success | "
                        f"Size: {len(image_content)//1024}KB | Type: {file_ext}"
                    )

                except Exception as e:
                    upload_errors += 1
                    logger.error(
                        f"Upload [{idx}/{len(content_pieces)}] | Error: {str(e)[:100]}"
                    )
                    # Keep original URL on failure

        logger.debug(
            f"Storage upload summary | Success: {upload_success} | "
            f"Skipped: {upload_skipped} | Errors: {upload_errors} | "
            f"Total: {len(content_pieces)}"
        )

        return content_pieces

    def _save_to_database(
        self,
        db: Session,
        content_pieces: List[Dict[str, Any]]
    ) -> List[ContentPiece]:
        """Save content pieces to database with detailed logging"""

        saved_pieces = []
        save_errors = 0

        for idx, item in enumerate(content_pieces, 1):
            piece = item["content_piece"]

            try:
                db.add(piece)
                db.commit()
                db.refresh(piece)
                saved_pieces.append(piece)

                logger.debug(
                    f"Database save [{idx}/{len(content_pieces)}] | Success | "
                    f"ID: {piece.id} | Tier: {piece.access_tier}"
                )

            except Exception as e:
                save_errors += 1
                logger.error(
                    f"Database save [{idx}/{len(content_pieces)}] | "
                    f"Error: {str(e)[:100]}"
                )
                db.rollback()

        logger.debug(
            f"Database save summary | Saved: {len(saved_pieces)}/{len(content_pieces)} | "
            f"Errors: {save_errors}"
        )

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
