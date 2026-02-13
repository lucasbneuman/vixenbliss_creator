"""
Video Generation Service
Multi-provider video generation (E08-001) + Fallback system (E08-003)
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
import os
import asyncio

logger = logging.getLogger(__name__)



class VideoGenerationService:
    """
    Multi-provider video generation service

    Providers:
    - Runway Gen-3: High quality, $0.05/second
    - Pika Labs: Creative, $0.03/second
    - Luma Dream Machine: Fast, $0.02/second
    """

    def __init__(self):
        # Provider configurations
        self.providers = {
            "runway": {
                "name": "Runway Gen-3",
                "cost_per_second": 0.05,
                "quality": "high",
                "speed": "slow",
                "api_key_env": "RUNWAY_API_KEY",
                "base_url": "https://api.runwayml.com/v1"
            },
            "pika": {
                "name": "Pika Labs",
                "cost_per_second": 0.03,
                "quality": "medium",
                "speed": "medium",
                "api_key_env": "PIKA_API_KEY",
                "base_url": "https://api.pika.art/v1"
            },
            "luma": {
                "name": "Luma Dream Machine",
                "cost_per_second": 0.02,
                "quality": "medium",
                "speed": "fast",
                "api_key_env": "LUMA_API_KEY",
                "base_url": "https://api.lumalabs.ai/v1"
            }
        }

        # Fallback order (E08-003)
        self.fallback_order = ["luma", "pika", "runway"]

    async def generate_video(
        self,
        prompt: str,
        duration: int = 4,
        aspect_ratio: str = "16:9",
        style: Optional[str] = None,
        provider: Optional[str] = None,
        image_url: Optional[str] = None,
        enable_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Generate video with automatic provider selection and fallback

        Args:
            prompt: Video description/prompt
            duration: Video duration in seconds (default 4)
            aspect_ratio: Aspect ratio (16:9, 9:16, 1:1)
            style: Style preset (cinematic, realistic, artistic, etc.)
            provider: Specific provider to use (or auto-select)
            enable_fallback: Enable fallback to other providers on failure

        Returns:
            Video generation result with metadata
        """

        logger.info(f"Generating video: '{prompt[:50]}...' (duration: {duration}s, aspect_ratio: {aspect_ratio})")

        # Determine provider order
        if provider and provider in self.providers:
            provider_order = [provider]
            if enable_fallback:
                # Add other providers for fallback
                provider_order.extend([p for p in self.fallback_order if p != provider])
        else:
            provider_order = self.fallback_order.copy()

        # Filter providers that are not configured
        provider_order = [p for p in provider_order if self._is_provider_available(p)]

        last_error = None
        attempts = []

        for idx, provider_name in enumerate(provider_order):
            try:
                logger.info(f"Attempting video generation with {provider_name} (attempt {idx + 1}/{len(provider_order)})")

                result = await self._generate_with_provider(
                    provider=provider_name,
                    prompt=prompt,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                    style=style,
                    image_url=image_url
                )

                # Success!
                result["fallback_count"] = idx
                result["attempts"] = attempts

                logger.info(f"Video generated successfully with {provider_name}")

                return result

            except Exception as e:
                logger.error(f"Failed to generate video with {provider_name}: {str(e)}")

                attempts.append({
                    "provider": provider_name,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

                last_error = e

                # If last provider or fallback disabled, raise error
                if idx == len(provider_order) - 1 or not enable_fallback:
                    break

        # All providers failed
        raise Exception(f"All video providers failed. Last error: {str(last_error)}")

    async def _generate_with_provider(
        self,
        provider: str,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        style: Optional[str],
        image_url: Optional[str]
    ) -> Dict[str, Any]:
        """Generate video using specific provider"""

        provider_config = self.providers[provider]
        api_key = os.getenv(provider_config["api_key_env"])

        if not api_key:
            raise ValueError(f"API key not found for {provider}: {provider_config['api_key_env']}")

        # Call provider-specific method
        if provider == "runway":
            return await self._generate_runway(api_key, prompt, duration, aspect_ratio, style)
        elif provider == "pika":
            return await self._generate_pika(api_key, prompt, duration, aspect_ratio, style)
        elif provider == "luma":
            return await self._generate_luma(api_key, prompt, duration, aspect_ratio, style)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _generate_runway(
        self,
        api_key: str,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        style: Optional[str]
    ) -> Dict[str, Any]:
        """Generate video using Runway Gen-3"""

        base_url = self.providers["runway"]["base_url"]

        # Build request payload
        payload = {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "model": "gen3"
        }

        if style:
            payload["style"] = style

        async with httpx.AsyncClient(timeout=300.0) as client:
            # Submit generation request
            response = await client.post(
                f"{base_url}/generations",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()

            generation_data = response.json()
            generation_id = generation_data["id"]

            # Poll for completion (max 5 minutes)
            max_polls = 60
            poll_interval = 5

            for _ in range(max_polls):
                await asyncio.sleep(poll_interval)

                status_response = await client.get(
                    f"{base_url}/generations/{generation_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                status_response.raise_for_status()

                status_data = status_response.json()

                if status_data["status"] == "completed":
                    video_url = status_data["output"]["url"]

                    # Calculate cost
                    cost = duration * self.providers["runway"]["cost_per_second"]

                    return {
                        "provider": "runway",
                        "video_url": video_url,
                        "duration": duration,
                        "aspect_ratio": aspect_ratio,
                        "cost": cost,
                        "generation_id": generation_id,
                        "metadata": status_data
                    }

                elif status_data["status"] == "failed":
                    raise Exception(f"Runway generation failed: {status_data.get('error', 'Unknown error')}")

            raise Exception("Runway generation timed out")

    async def _generate_pika(
        self,
        api_key: str,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        style: Optional[str]
    ) -> Dict[str, Any]:
        """Generate video using Pika Labs"""

        base_url = self.providers["pika"]["base_url"]

        payload = {
            "prompt": prompt,
            "num_frames": duration * 24,  # 24 fps
            "aspect_ratio": aspect_ratio
        }

        if style:
            payload["style"] = style

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{base_url}/generate",
                json=payload,
                headers={"X-API-Key": api_key}
            )
            response.raise_for_status()

            generation_data = response.json()
            job_id = generation_data["job_id"]

            # Poll for completion
            max_polls = 60
            poll_interval = 5

            for _ in range(max_polls):
                await asyncio.sleep(poll_interval)

                status_response = await client.get(
                    f"{base_url}/jobs/{job_id}",
                    headers={"X-API-Key": api_key}
                )
                status_response.raise_for_status()

                status_data = status_response.json()

                if status_data["status"] == "succeeded":
                    video_url = status_data["result"]["video_url"]

                    cost = duration * self.providers["pika"]["cost_per_second"]

                    return {
                        "provider": "pika",
                        "video_url": video_url,
                        "duration": duration,
                        "aspect_ratio": aspect_ratio,
                        "cost": cost,
                        "generation_id": job_id,
                        "metadata": status_data
                    }

                elif status_data["status"] == "failed":
                    raise Exception(f"Pika generation failed: {status_data.get('error', 'Unknown error')}")

            raise Exception("Pika generation timed out")

    async def _generate_luma(
        self,
        api_key: str,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        style: Optional[str]
    ) -> Dict[str, Any]:
        """Generate video using Luma Dream Machine"""

        base_url = self.providers["luma"]["base_url"]

        payload = {
            "prompt": prompt,
            "keyframes": {
                "frame0": {"type": "generation"}
            },
            "aspect_ratio": aspect_ratio,
            "loop": False
        }

        if style:
            payload["style"] = style

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{base_url}/generations",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()

            generation_data = response.json()
            generation_id = generation_data["id"]

            # Poll for completion
            max_polls = 60
            poll_interval = 5

            for _ in range(max_polls):
                await asyncio.sleep(poll_interval)

                status_response = await client.get(
                    f"{base_url}/generations/{generation_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                status_response.raise_for_status()

                status_data = status_response.json()

                if status_data["state"] == "completed":
                    video_url = status_data["assets"]["video"]

                    cost = duration * self.providers["luma"]["cost_per_second"]

                    return {
                        "provider": "luma",
                        "video_url": video_url,
                        "duration": duration,
                        "aspect_ratio": aspect_ratio,
                        "cost": cost,
                        "generation_id": generation_id,
                        "metadata": status_data
                    }

                elif status_data["state"] == "failed":
                    raise Exception(f"Luma generation failed: {status_data.get('failure_reason', 'Unknown error')}")

            raise Exception("Luma generation timed out")

    def select_optimal_provider(
        self,
        budget: Optional[float] = None,
        priority: str = "balanced"
    ) -> str:
        """
        Select optimal provider based on criteria

        Args:
            budget: Budget per second
            priority: Selection priority (quality, speed, cost, balanced)

        Returns:
            Recommended provider name
        """

        if priority == "quality":
            return "runway"
        elif priority == "speed":
            return "luma"
        elif priority == "cost":
            return "luma"
        elif priority == "balanced":
            return "pika"

        # Budget-based selection
        if budget:
            if budget >= 0.05:
                return "runway"
            elif budget >= 0.03:
                return "pika"
            else:
                return "luma"

        return "pika"  # Default to balanced

    def _is_provider_available(self, provider: str) -> bool:
        provider_config = self.providers.get(provider, {})
        api_key_env = provider_config.get("api_key_env")
        if not api_key_env:
            return False
        return bool(os.getenv(api_key_env))


# Singleton instance
video_generation_service = VideoGenerationService()
