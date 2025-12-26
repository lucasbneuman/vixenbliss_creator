"""
Content Safety Layer
NSFW detection and content moderation using OpenAI Moderation API
"""

import os
import httpx
from typing import Dict, Any, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SafetyRating(str, Enum):
    SAFE = "safe"  # Capa 1: Safe for all platforms
    SUGGESTIVE = "suggestive"  # Capa 2: Premium content, some platforms
    BORDERLINE = "borderline"  # Capa 3: Explicit, restricted platforms only
    REJECTED = "rejected"  # Too explicit, reject


class SafetyCategory(str, Enum):
    SEXUAL = "sexual"
    VIOLENCE = "violence"
    HATE = "hate"
    SELF_HARM = "self_harm"
    HARASSMENT = "harassment"


class ContentSafetyService:
    """Service for content safety and moderation"""

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.moderation_url = "https://api.openai.com/v1/moderations"

        # Safety thresholds for automatic rejection
        self.rejection_thresholds = {
            SafetyCategory.SEXUAL: 0.90,  # High threshold (artistic nudity OK)
            SafetyCategory.VIOLENCE: 0.70,
            SafetyCategory.HATE: 0.50,
            SafetyCategory.SELF_HARM: 0.50,
            SafetyCategory.HARASSMENT: 0.60
        }

        # Thresholds for tier classification
        self.tier_thresholds = {
            "capa1": {  # Safe for Instagram, TikTok
                SafetyCategory.SEXUAL: 0.20,
                SafetyCategory.VIOLENCE: 0.10,
                SafetyCategory.HATE: 0.05,
            },
            "capa2": {  # Suggestive, premium platforms
                SafetyCategory.SEXUAL: 0.60,
                SafetyCategory.VIOLENCE: 0.30,
                SafetyCategory.HATE: 0.10,
            },
            "capa3": {  # Explicit, OnlyFans only
                SafetyCategory.SEXUAL: 0.90,
                SafetyCategory.VIOLENCE: 0.50,
                SafetyCategory.HATE: 0.20,
            }
        }

    async def check_image_safety(
        self,
        image_url: str,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check image safety using OpenAI Moderation API

        Args:
            image_url: URL of image to check
            prompt: Optional prompt used to generate image

        Returns:
            Safety analysis with rating, scores, and tier classification
        """

        # Check text prompt first (if provided)
        text_safety = None
        if prompt:
            text_safety = await self._check_text_safety(prompt)

        # Note: OpenAI Moderation API v1 doesn't support images directly
        # For image moderation, we use the prompt as proxy
        # In production, integrate with dedicated image moderation (AWS Rekognition, Google Vision, etc.)

        # If text is rejected, reject image
        if text_safety and text_safety["rating"] == SafetyRating.REJECTED:
            return {
                "rating": SafetyRating.REJECTED,
                "access_tier": None,
                "scores": text_safety["scores"],
                "flagged_categories": text_safety["flagged_categories"],
                "safe": False,
                "reason": "Prompt content violates safety policies",
                "text_safety": text_safety
            }

        # Use prompt safety as image safety proxy
        if text_safety:
            rating, tier = self._classify_content(text_safety["scores"])

            return {
                "rating": rating,
                "access_tier": tier,
                "scores": text_safety["scores"],
                "flagged_categories": text_safety["flagged_categories"],
                "safe": rating != SafetyRating.REJECTED,
                "text_safety": text_safety,
                "note": "Image safety based on prompt analysis"
            }

        # No prompt provided - default to safe (should integrate real image moderation)
        return {
            "rating": SafetyRating.SAFE,
            "access_tier": "capa1",
            "scores": {},
            "flagged_categories": [],
            "safe": True,
            "note": "No safety check performed - integrate image moderation service"
        }

    async def _check_text_safety(self, text: str) -> Dict[str, Any]:
        """Check text content using OpenAI Moderation API"""

        if not self.openai_key:
            logger.warning("OpenAI API key not configured, skipping safety check")
            return {
                "rating": SafetyRating.SAFE,
                "scores": {},
                "flagged_categories": [],
                "safe": True
            }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.moderation_url,
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": text,
                        "model": "omni-moderation-latest"  # Latest moderation model
                    },
                    timeout=30.0
                )

                response.raise_for_status()
                data = response.json()

                result = data["results"][0]

                # Extract category scores
                scores = {
                    SafetyCategory.SEXUAL: result["category_scores"].get("sexual", 0),
                    SafetyCategory.VIOLENCE: result["category_scores"].get("violence", 0),
                    SafetyCategory.HATE: result["category_scores"].get("hate", 0),
                    SafetyCategory.SELF_HARM: result["category_scores"].get("self-harm", 0),
                    SafetyCategory.HARASSMENT: result["category_scores"].get("harassment", 0)
                }

                # Find flagged categories
                flagged_categories = []
                for category, score in scores.items():
                    if score > self.rejection_thresholds.get(category, 0.5):
                        flagged_categories.append(category)

                # Determine rating
                rating, tier = self._classify_content(scores)

                return {
                    "rating": rating,
                    "access_tier": tier,
                    "scores": {k.value: v for k, v in scores.items()},
                    "flagged_categories": [c.value for c in flagged_categories],
                    "safe": rating != SafetyRating.REJECTED,
                    "raw_result": result
                }

            except Exception as e:
                logger.error(f"Safety check failed: {str(e)}")
                # Fail safe: reject on error
                return {
                    "rating": SafetyRating.REJECTED,
                    "scores": {},
                    "flagged_categories": ["error"],
                    "safe": False,
                    "error": str(e)
                }

    def _classify_content(
        self,
        scores: Dict[SafetyCategory, float]
    ) -> Tuple[SafetyRating, Optional[str]]:
        """
        Classify content into safety rating and access tier

        Args:
            scores: Category scores from moderation API

        Returns:
            (SafetyRating, access_tier)
        """

        # Check for rejection
        for category, score in scores.items():
            threshold = self.rejection_thresholds.get(category, 0.5)
            if score > threshold:
                return SafetyRating.REJECTED, None

        # Check tier classification
        sexual_score = scores.get(SafetyCategory.SEXUAL, 0)
        violence_score = scores.get(SafetyCategory.VIOLENCE, 0)
        hate_score = scores.get(SafetyCategory.HATE, 0)

        # Capa 1: Safe for all platforms
        if (sexual_score <= self.tier_thresholds["capa1"][SafetyCategory.SEXUAL] and
            violence_score <= self.tier_thresholds["capa1"][SafetyCategory.VIOLENCE] and
            hate_score <= self.tier_thresholds["capa1"][SafetyCategory.HATE]):
            return SafetyRating.SAFE, "capa1"

        # Capa 2: Suggestive, premium content
        if (sexual_score <= self.tier_thresholds["capa2"][SafetyCategory.SEXUAL] and
            violence_score <= self.tier_thresholds["capa2"][SafetyCategory.VIOLENCE] and
            hate_score <= self.tier_thresholds["capa2"][SafetyCategory.HATE]):
            return SafetyRating.SUGGESTIVE, "capa2"

        # Capa 3: Explicit, restricted platforms
        if (sexual_score <= self.tier_thresholds["capa3"][SafetyCategory.SEXUAL] and
            violence_score <= self.tier_thresholds["capa3"][SafetyCategory.VIOLENCE] and
            hate_score <= self.tier_thresholds["capa3"][SafetyCategory.HATE]):
            return SafetyRating.BORDERLINE, "capa3"

        # Borderline case (close to rejection)
        return SafetyRating.BORDERLINE, "capa3"

    async def batch_check_safety(
        self,
        items: list[Dict[str, str]]
    ) -> list[Dict[str, Any]]:
        """
        Check safety for batch of content

        Args:
            items: List of dicts with 'image_url' and optional 'prompt'

        Returns:
            List of safety check results
        """

        import asyncio

        tasks = [
            self.check_image_safety(
                image_url=item["image_url"],
                prompt=item.get("prompt")
            )
            for item in items
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "rating": SafetyRating.REJECTED,
                    "safe": False,
                    "error": str(result),
                    "index": idx
                })
            else:
                result["index"] = idx
                processed_results.append(result)

        return processed_results

    def filter_safe_content(
        self,
        content_list: list[Dict[str, Any]],
        safety_results: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Filter content to only include safe items

        Args:
            content_list: List of content items
            safety_results: List of safety check results

        Returns:
            Filtered list with only safe content
        """

        safe_content = []

        for content, safety in zip(content_list, safety_results):
            if safety.get("safe", False) and safety.get("rating") != SafetyRating.REJECTED:
                # Add safety metadata to content
                content["safety_rating"] = safety["rating"]
                content["access_tier"] = safety["access_tier"]
                content["safety_scores"] = safety.get("scores", {})
                safe_content.append(content)

        return safe_content

    def get_platform_compatible_content(
        self,
        content_list: list[Dict[str, Any]],
        platform: str
    ) -> list[Dict[str, Any]]:
        """
        Filter content compatible with specific platform

        Args:
            content_list: List of content with safety ratings
            platform: Platform name (instagram, tiktok, onlyfans)

        Returns:
            Platform-compatible content
        """

        platform_tiers = {
            "instagram": ["capa1"],
            "tiktok": ["capa1"],
            "twitter": ["capa1", "capa2"],
            "onlyfans": ["capa1", "capa2", "capa3"]
        }

        allowed_tiers = platform_tiers.get(platform.lower(), ["capa1"])

        return [
            content for content in content_list
            if content.get("access_tier") in allowed_tiers
        ]

    def estimate_safety_check_cost(self, num_checks: int) -> float:
        """
        Estimate cost for safety checks

        Args:
            num_checks: Number of safety checks

        Returns:
            Estimated cost in USD
        """

        # OpenAI Moderation API: Free
        # For production image moderation (AWS Rekognition): ~$0.001 per image
        cost_per_check = 0.0001  # Minimal cost for text moderation

        return num_checks * cost_per_check


# Singleton instance
content_safety_service = ContentSafetyService()
