"""
AI Provider Integration Service
Multi-provider support for image generation with intelligent routing
"""

import os
import time
import httpx
import replicate
from typing import Optional, Dict, Any, Tuple
from enum import Enum

from app.schemas.identity import ProviderType, FacialGenerationRequest, FacialMetadata


class ProviderPriority(Enum):
    """Provider priority based on cost/quality tradeoff"""
    REPLICATE_SDXL = 1  # Fast, cheap, good quality
    LEONARDO = 2        # Medium cost, great quality
    MIDJOURNEY = 3      # Expensive, best quality
    DALL_E_3 = 4        # Fallback, reliable


# Provider pricing (USD per image)
PROVIDER_PRICING = {
    "replicate_sdxl": 0.01,
    "leonardo": 0.025,
    "midjourney": 0.08,
    "dall_e_3": 0.04
}


class AIProviderService:
    """Handles multi-provider AI image generation"""

    def __init__(self):
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        self.leonardo_key = os.getenv("LEONARDO_API_KEY")
        self.midjourney_key = os.getenv("MIDJOURNEY_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

    def _build_prompt(self, request: FacialGenerationRequest) -> str:
        """Build optimized prompt for facial generation"""
        age_descriptors = {
            "18-25": "youthful, fresh-faced",
            "26-35": "mature, confident",
            "36-45": "refined, sophisticated",
            "46+": "elegant, distinguished"
        }

        base_prompt = (
            f"Professional photorealistic portrait of a {age_descriptors[request.age_range]} "
            f"{request.gender}, {request.ethnicity} features, {request.aesthetic_style} style, "
            f"high quality photography, studio lighting, sharp focus, 8k resolution"
        )

        if request.custom_prompt:
            base_prompt += f", {request.custom_prompt}"

        # Negative prompt
        negative = (
            "cartoon, anime, 3d render, illustration, painting, drawing, "
            "unrealistic, distorted, blurry, low quality, watermark, text"
        )

        return base_prompt, negative

    async def generate_via_replicate(
        self,
        request: FacialGenerationRequest
    ) -> Tuple[str, Dict[str, Any], float]:
        """Generate image using Replicate SDXL"""
        prompt, negative = self._build_prompt(request)

        start_time = time.time()

        try:
            output = await replicate.async_run(
                "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                input={
                    "prompt": prompt,
                    "negative_prompt": negative,
                    "num_outputs": 1,
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5,
                    "width": 1024,
                    "height": 1024,
                    "scheduler": "DPMSolverMultistep"
                }
            )

            generation_time = time.time() - start_time

            image_url = output[0] if isinstance(output, list) else output

            params = {
                "model": "sdxl",
                "steps": 30,
                "cfg_scale": 7.5,
                "resolution": "1024x1024"
            }

            return image_url, params, generation_time

        except Exception as e:
            raise Exception(f"Replicate SDXL generation failed: {str(e)}")

    async def generate_via_leonardo(
        self,
        request: FacialGenerationRequest
    ) -> Tuple[str, Dict[str, Any], float]:
        """Generate image using Leonardo.ai"""
        if not self.leonardo_key:
            raise ValueError("Leonardo API key not configured")

        prompt, _ = self._build_prompt(request)

        start_time = time.time()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://cloud.leonardo.ai/api/rest/v1/generations",
                    headers={
                        "Authorization": f"Bearer {self.leonardo_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": prompt,
                        "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",  # Leonardo Phoenix
                        "width": 1024,
                        "height": 1024,
                        "num_images": 1,
                        "photoReal": True,
                        "alchemy": True
                    },
                    timeout=120.0
                )

                response.raise_for_status()
                data = response.json()

                # Poll for completion
                generation_id = data["sdGenerationJob"]["generationId"]
                image_url = await self._poll_leonardo_generation(client, generation_id)

                generation_time = time.time() - start_time

                params = {
                    "model": "leonardo_phoenix",
                    "photo_real": True,
                    "alchemy": True
                }

                return image_url, params, generation_time

            except Exception as e:
                raise Exception(f"Leonardo generation failed: {str(e)}")

    async def _poll_leonardo_generation(self, client: httpx.AsyncClient, generation_id: str) -> str:
        """Poll Leonardo API until generation is complete"""
        max_attempts = 60
        attempt = 0

        while attempt < max_attempts:
            response = await client.get(
                f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}",
                headers={"Authorization": f"Bearer {self.leonardo_key}"}
            )

            data = response.json()

            if data["generations_by_pk"]["status"] == "COMPLETE":
                return data["generations_by_pk"]["generated_images"][0]["url"]

            await asyncio.sleep(2)
            attempt += 1

        raise TimeoutError("Leonardo generation timed out")

    async def generate_via_dall_e(
        self,
        request: FacialGenerationRequest
    ) -> Tuple[str, Dict[str, Any], float]:
        """Generate image using DALL-E 3 (fallback)"""
        if not self.openai_key:
            raise ValueError("OpenAI API key not configured")

        prompt, _ = self._build_prompt(request)

        start_time = time.time()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": "1024x1024",
                        "quality": "hd",
                        "style": "natural"
                    },
                    timeout=60.0
                )

                response.raise_for_status()
                data = response.json()

                generation_time = time.time() - start_time

                image_url = data["data"][0]["url"]

                params = {
                    "model": "dall-e-3",
                    "quality": "hd",
                    "style": "natural"
                }

                return image_url, params, generation_time

            except Exception as e:
                raise Exception(f"DALL-E 3 generation failed: {str(e)}")

    async def generate_with_routing(
        self,
        request: FacialGenerationRequest
    ) -> Tuple[str, FacialMetadata, float, ProviderType]:
        """
        Intelligent provider routing:
        1. Use specified provider if available
        2. Fall back to priority order
        3. Return image URL, metadata, cost, and provider used
        """

        # Determine provider order
        if request.provider:
            providers_to_try = [request.provider]
        else:
            # Default priority: SDXL -> Leonardo -> DALL-E
            providers_to_try = ["replicate_sdxl", "leonardo", "dall_e_3"]

        last_error = None

        for provider in providers_to_try:
            try:
                if provider == "replicate_sdxl" and self.replicate_token:
                    image_url, params, gen_time = await self.generate_via_replicate(request)
                elif provider == "leonardo" and self.leonardo_key:
                    image_url, params, gen_time = await self.generate_via_leonardo(request)
                elif provider == "dall_e_3" and self.openai_key:
                    image_url, params, gen_time = await self.generate_via_dall_e(request)
                else:
                    continue  # Provider not configured

                # Build metadata
                metadata = FacialMetadata(
                    age=self._estimate_age_from_range(request.age_range),
                    ethnicity=request.ethnicity or "diverse",
                    aesthetic_style=request.aesthetic_style,
                    dominant_features=[],  # TODO: Extract via CLIP
                    quality_score=0.85,  # TODO: Calculate actual quality score
                    provider_used=provider,
                    generation_params=params
                )

                cost = PROVIDER_PRICING.get(provider, 0.02)

                return image_url, metadata, cost, provider

            except Exception as e:
                last_error = e
                continue

        # All providers failed
        raise Exception(f"All providers failed. Last error: {str(last_error)}")

    def _estimate_age_from_range(self, age_range: str) -> int:
        """Estimate median age from range"""
        ranges = {
            "18-25": 22,
            "26-35": 30,
            "36-45": 40,
            "46+": 50
        }
        return ranges.get(age_range, 30)


# Singleton instance
ai_provider_service = AIProviderService()
