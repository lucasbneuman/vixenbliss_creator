"""
Premium Packs Service
Generate and manage premium content packs (Capa 2) - E07-001
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID
import random

from app.models.content_piece import ContentPiece
from app.models.avatar import Avatar
from app.services.lora_inference import lora_inference_service
from app.services.template_library import template_library
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


class PremiumPacksService:
    """
    Service for creating and managing premium content packs (Capa 2)

    Premium tiers:
    - Capa 1: $9.99/month - Soft content (explicitness 1-3)
    - Capa 2: $29-149 - Premium packs with explicit content (explicitness 4-8)
    - Capa 3: $199+ - Custom content requests (explicitness 9-10)
    """

    def __init__(self):
        # Premium pack configurations
        self.pack_configs = {
            "starter_pack": {
                "name": "Starter Premium Pack",
                "price": 29.99,
                "piece_count": 10,
                "explicitness_range": (4, 5),
                "description": "10 exclusive premium photos"
            },
            "deluxe_pack": {
                "name": "Deluxe Premium Pack",
                "price": 59.99,
                "piece_count": 25,
                "explicitness_range": (5, 6),
                "description": "25 high-quality premium photos"
            },
            "ultimate_pack": {
                "name": "Ultimate Premium Pack",
                "price": 99.99,
                "piece_count": 50,
                "explicitness_range": (6, 7),
                "description": "50 exclusive premium photos"
            },
            "vip_pack": {
                "name": "VIP Premium Pack",
                "price": 149.99,
                "piece_count": 100,
                "explicitness_range": (7, 8),
                "description": "100 premium photos + bonus content"
            }
        }

        # Premium template categories (more explicit)
        self.premium_categories = [
            "lingerie",
            "bedroom",
            "shower",
            "poolside",
            "intimate",
            "boudoir",
            "artistic_nude",
            "glamour"
        ]

    async def create_premium_pack(
        self,
        db: Session,
        avatar_id: UUID,
        pack_type: str = "deluxe_pack",
        custom_piece_count: Optional[int] = None,
        custom_price: Optional[float] = None,
        custom_explicitness: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a premium content pack for an avatar

        Args:
            db: Database session
            avatar_id: Avatar ID
            pack_type: Pack configuration (starter_pack, deluxe_pack, etc.)
            custom_piece_count: Override piece count
            custom_price: Override price
            custom_explicitness: Override explicitness level (4-8)

        Returns:
            Pack creation result with content piece IDs
        """

        logger.info(f"Creating premium pack '{pack_type}' for avatar {avatar_id}")

        # Get avatar
        avatar = db.query(Avatar).filter(Avatar.id == avatar_id).first()

        if not avatar:
            raise ValueError(f"Avatar {avatar_id} not found")

        if not avatar.lora_weights_url:
            raise ValueError(f"Avatar {avatar_id} needs trained LoRA weights")

        # Get pack configuration
        pack_config = self.pack_configs.get(pack_type)

        if not pack_config:
            raise ValueError(f"Unknown pack type: {pack_type}")

        # Apply custom overrides
        piece_count = custom_piece_count or pack_config["piece_count"]
        price_per_piece = (custom_price or pack_config["price"]) / piece_count
        explicitness_min, explicitness_max = pack_config["explicitness_range"]

        if custom_explicitness:
            explicitness_min = explicitness_max = custom_explicitness

        # Select premium templates
        templates = self._select_premium_templates(
            avatar_niche=avatar.niche or "lifestyle",
            count=piece_count
        )

        # Generate premium content pieces
        content_pieces = []
        total_cost = 0.0

        for idx, template in enumerate(templates):
            # Randomize explicitness within range
            explicitness = random.randint(explicitness_min, explicitness_max)

            # Generate prompt with explicitness adjustment
            enhanced_prompt = self._enhance_prompt_for_premium(
                base_prompt=template["prompt"],
                explicitness_level=explicitness,
                avatar_style=avatar.aesthetic_style or "natural"
            )

            # Generate image using LoRA
            result = await lora_inference_service.generate_image_with_lora(
                lora_weights_url=avatar.lora_weights_url,
                prompt=enhanced_prompt,
                negative_prompt=template.get("negative_prompt", ""),
                style=template["style"]
            )

            # Upload to R2 storage
            r2_url = await storage_service.upload_content_piece(
                avatar_id=avatar_id,
                content_data=result["image_data"],
                content_type="image",
                tier="capa2"
            )

            # Create content piece record
            content_piece = ContentPiece(
                avatar_id=avatar_id,
                content_type="image",
                access_tier="capa2",
                url=r2_url,
                explicitness_level=explicitness,
                price_usd=price_per_piece,
                metadata={
                    "template_id": template["id"],
                    "template_category": template["category"],
                    "pack_type": pack_type,
                    "generation_params": {
                        "model": result.get("model"),
                        "steps": result.get("steps"),
                        "guidance_scale": result.get("guidance_scale")
                    }
                },
                safety_rating="premium"
            )

            db.add(content_piece)
            content_pieces.append(content_piece)

            total_cost += result.get("cost", 0.0)

            logger.info(f"Generated premium content piece {idx + 1}/{piece_count} (explicitness: {explicitness})")

        db.commit()

        # Refresh all pieces to get IDs
        for piece in content_pieces:
            db.refresh(piece)

        logger.info(f"Created premium pack with {len(content_pieces)} pieces, total cost: ${total_cost:.2f}")

        return {
            "pack_type": pack_type,
            "pack_name": pack_config["name"],
            "total_pieces": len(content_pieces),
            "pack_price": custom_price or pack_config["price"],
            "price_per_piece": price_per_piece,
            "total_generation_cost": round(total_cost, 2),
            "explicitness_range": [explicitness_min, explicitness_max],
            "content_piece_ids": [str(p.id) for p in content_pieces],
            "created_at": datetime.utcnow().isoformat()
        }

    def _select_premium_templates(
        self,
        avatar_niche: str,
        count: int
    ) -> List[Dict[str, Any]]:
        """Select premium templates from premium categories"""

        # Get all templates from premium categories
        premium_templates = []

        for category in self.premium_categories:
            category_templates = template_library.get_templates_by_category(category)
            premium_templates.extend(category_templates)

        # If not enough premium templates, get suggestive ones
        if len(premium_templates) < count:
            suggestive_cats = ["fitness", "beach", "glamour"]
            for cat in suggestive_cats:
                premium_templates.extend(template_library.get_templates_by_category(cat))

        # Shuffle and select
        random.shuffle(premium_templates)

        return premium_templates[:count]

    def _enhance_prompt_for_premium(
        self,
        base_prompt: str,
        explicitness_level: int,
        avatar_style: str
    ) -> str:
        """
        Enhance prompt based on explicitness level

        Levels:
        1-3: Soft (Capa 1) - clothed, suggestive
        4-5: Premium entry (Capa 2) - lingerie, partial
        6-7: Premium deluxe (Capa 2) - minimal clothing, artistic
        8: Premium VIP (Capa 2) - explicit artistic
        9-10: Custom (Capa 3) - fully explicit
        """

        # Base quality enhancers
        quality_tags = "professional photography, high quality, 8k uhd, dslr, sharp focus"

        # Explicitness modifiers
        if explicitness_level <= 3:
            # Soft content (shouldn't reach here for premium packs)
            explicitness_tags = "clothed, suggestive pose, elegant"

        elif explicitness_level <= 5:
            # Premium entry
            explicitness_tags = "lingerie, seductive, intimate setting, soft lighting"

        elif explicitness_level <= 7:
            # Premium deluxe
            explicitness_tags = "minimal clothing, artistic pose, sensual, boudoir photography, dramatic lighting"

        else:  # 8+
            # Premium VIP
            explicitness_tags = "artistic nude photography, tasteful, fine art style, professional boudoir"

        # Style enhancements
        style_tags = ""
        if avatar_style == "natural":
            style_tags = "natural beauty, realistic skin texture, authentic"
        elif avatar_style == "glamorous":
            style_tags = "glamorous, polished, luxurious, high-end"
        elif avatar_style == "artistic":
            style_tags = "artistic composition, creative lighting, fine art"

        # Combine
        enhanced_prompt = f"{base_prompt}, {explicitness_tags}, {style_tags}, {quality_tags}"

        return enhanced_prompt

    def get_available_packs(
        self,
        db: Session,
        avatar_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get list of available premium packs for an avatar

        Args:
            db: Database session
            avatar_id: Avatar ID

        Returns:
            List of available pack configurations
        """

        avatar = db.query(Avatar).filter(Avatar.id == avatar_id).first()

        if not avatar:
            raise ValueError(f"Avatar {avatar_id} not found")

        available_packs = []

        for pack_key, pack_config in self.pack_configs.items():
            available_packs.append({
                "pack_id": pack_key,
                "name": pack_config["name"],
                "description": pack_config["description"],
                "price": pack_config["price"],
                "piece_count": pack_config["piece_count"],
                "price_per_piece": round(pack_config["price"] / pack_config["piece_count"], 2),
                "explicitness_range": pack_config["explicitness_range"],
                "available": bool(avatar.lora_weights_url)
            })

        return available_packs

    def get_pack_statistics(
        self,
        db: Session,
        avatar_id: UUID
    ) -> Dict[str, Any]:
        """
        Get statistics for premium packs created for an avatar

        Args:
            db: Database session
            avatar_id: Avatar ID

        Returns:
            Statistics dictionary
        """

        # Get all Capa 2 content pieces
        premium_pieces = db.query(ContentPiece).filter(
            ContentPiece.avatar_id == avatar_id,
            ContentPiece.access_tier == "capa2"
        ).all()

        if not premium_pieces:
            return {
                "total_premium_pieces": 0,
                "total_pack_value": 0.0,
                "average_explicitness": 0.0,
                "packs_created": []
            }

        # Group by pack type
        packs_created = {}
        for piece in premium_pieces:
            pack_type = piece.metadata.get("pack_type", "unknown")

            if pack_type not in packs_created:
                packs_created[pack_type] = {
                    "pack_type": pack_type,
                    "piece_count": 0,
                    "total_value": 0.0
                }

            packs_created[pack_type]["piece_count"] += 1
            packs_created[pack_type]["total_value"] += piece.price_usd or 0.0

        total_value = sum(p.price_usd or 0.0 for p in premium_pieces)
        avg_explicitness = sum(p.explicitness_level or 0 for p in premium_pieces) / len(premium_pieces)

        return {
            "total_premium_pieces": len(premium_pieces),
            "total_pack_value": round(total_value, 2),
            "average_explicitness": round(avg_explicitness, 1),
            "packs_created": list(packs_created.values())
        }


# Singleton instance
premium_packs_service = PremiumPacksService()
