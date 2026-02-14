"""
AI Provider Integration Service
Multi-provider support for image generation with intelligent routing
"""

import os
import time
import asyncio
import base64
from io import BytesIO
import httpx
import replicate
from typing import Dict, Any, Tuple, Callable, List
from enum import Enum
from PIL import Image, ImageDraw

from app.schemas.identity import ProviderType, FacialGenerationRequest, FacialMetadata
from app.services.modal_sdxl_lora_client import modal_sdxl_lora_client


class ProviderPriority(Enum):
    """Provider priority based on cost/quality tradeoff"""
    MODAL_SDXL_LORA = 0
    REPLICATE_SDXL = 1
    LEONARDO = 2
    MIDJOURNEY = 3
    DALL_E_3 = 4


# Provider pricing (USD per image)
PROVIDER_PRICING = {
    "modal_sdxl_lora": 0.001,
    "replicate_sdxl": 0.01,
    "leonardo": 0.025,
    "midjourney": 0.08,
    "dall_e_3": 0.04,
}


class AIProviderService:
    """Handles multi-provider AI image generation"""

    def __init__(self):
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        self.leonardo_key = os.getenv("LEONARDO_API_KEY")
        self.midjourney_key = os.getenv("MIDJOURNEY_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.modal_endpoint_url = (
            os.getenv("AI_PROVIDER_ENDPOINT_URL")
            or os.getenv("MODAL_ENDPOINT_URL")
        )
        self.provider_aliases = {
            "modal": "modal_sdxl_lora",
            "modal_sdxl_lora": "modal_sdxl_lora",
            "replicate": "replicate_sdxl",
            "replicate_sdxl": "replicate_sdxl",
            "leonardo": "leonardo",
            "openai": "dall_e_3",
            "dall_e_3": "dall_e_3",
            "dalle3": "dall_e_3",
        }

    def _resolve_provider(self, provider: str) -> str:
        return self.provider_aliases.get(provider.lower(), provider.lower())

    def _default_provider_order(self) -> List[str]:
        configured = os.getenv("FACE_PROVIDER_ORDER", "").strip()
        if configured:
            return [
                self._resolve_provider(provider)
                for provider in configured.split(",")
                if provider.strip()
            ]
        return ["modal_sdxl_lora", "replicate_sdxl", "leonardo", "dall_e_3"]

    def _is_provider_available(self, provider: str) -> bool:
        if provider == "modal_sdxl_lora":
            return bool(self.modal_endpoint_url)
        if provider == "replicate_sdxl":
            return bool(self.replicate_token)
        if provider == "leonardo":
            return bool(self.leonardo_key)
        if provider == "dall_e_3":
            return bool(self.openai_key)
        return False

    def _provider_handler(self, provider: str) -> Callable[[FacialGenerationRequest], Any]:
        handlers: Dict[str, Callable[[FacialGenerationRequest], Any]] = {
            "modal_sdxl_lora": self.generate_via_modal_sdxl_lora,
            "replicate_sdxl": self.generate_via_replicate,
            "leonardo": self.generate_via_leonardo,
            "dall_e_3": self.generate_via_dall_e,
        }
        if provider not in handlers:
            raise ValueError(f"Unknown face provider: {provider}")
        return handlers[provider]

    def _build_prompt(self, request: FacialGenerationRequest) -> Tuple[str, str]:
        """Build optimized prompt for facial generation"""
        age_descriptors = {
            "18-25": "youthful, fresh-faced",
            "26-35": "mature, confident",
            "36-45": "refined, sophisticated",
            "46+": "elegant, distinguished",
        }

        base_prompt = (
            f"Professional photorealistic portrait of a {age_descriptors[request.age_range]} "
            f"{request.gender}, {request.ethnicity} features, {request.aesthetic_style} style, "
            "high quality photography, studio lighting, sharp focus, 8k resolution"
        )

        if request.custom_prompt:
            base_prompt += f", {request.custom_prompt}"

        negative = (
            "cartoon, anime, 3d render, illustration, painting, drawing, "
            "unrealistic, distorted, blurry, low quality, watermark, text"
        )

        return base_prompt, negative

    def _generate_local_placeholder(
        self,
        request: FacialGenerationRequest,
    ) -> Tuple[str, Dict[str, Any], float]:
        """
        Generate a local placeholder image when no external provider is configured.
        This keeps local/dev flows working without paid API keys.
        """
        start_time = time.time()

        # Simple branded placeholder (1024x1024) to avoid external API dependency.
        img = Image.new("RGB", (1024, 1024), color=(40, 36, 52))
        draw = ImageDraw.Draw(img)

        lines = [
            "VixenBliss Local Avatar",
            f"style: {request.aesthetic_style}",
            f"gender: {request.gender}",
            f"age: {request.age_range}",
        ]

        y = 420
        for line in lines:
            draw.text((180, y), line, fill=(245, 245, 245))
            y += 60

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        image_url = f"data:image/png;base64,{image_b64}"

        generation_time = time.time() - start_time
        params = {
            "model": "local_placeholder",
            "resolution": "1024x1024",
            "fallback_reason": "no_provider_keys_configured",
        }
        return image_url, params, generation_time

    async def generate_via_modal_sdxl_lora(
        self,
        request: FacialGenerationRequest,
    ) -> Tuple[str, Dict[str, Any], float]:
        """Generate image using Modal SDXL 1.0 endpoint."""
        prompt, negative = self._build_prompt(request)

        result = await modal_sdxl_lora_client.generate_image_with_lora(
            prompt=prompt,
            negative_prompt=negative,
            width=1024,
            height=1024,
            steps=30,
            cfg=7.5,
            lora_url=None,
        )

        image_base64 = result.get("image_base64")
        if not image_base64:
            raise ValueError("Modal SDXL response missing image_base64")

        image_url = f"data:image/png;base64,{image_base64}"
        params = {
            "model": "sdxl_1.0",
            "steps": 30,
            "cfg_scale": 7.5,
            "resolution": "1024x1024",
            "provider_backend": "modal_sdxl_lora",
        }
        return image_url, params, float(result.get("generation_time", 0.0))

    async def generate_via_replicate(
        self,
        request: FacialGenerationRequest,
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
                    "scheduler": "DPMSolverMultistep",
                },
            )

            generation_time = time.time() - start_time
            image_url = output[0] if isinstance(output, list) else output

            params = {
                "model": "sdxl",
                "steps": 30,
                "cfg_scale": 7.5,
                "resolution": "1024x1024",
            }

            return image_url, params, generation_time

        except Exception as e:
            raise Exception(f"Replicate SDXL generation failed: {str(e)}")

    async def generate_via_leonardo(
        self,
        request: FacialGenerationRequest,
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
                        "Content-Type": "application/json",
                    },
                    json={
                        "prompt": prompt,
                        "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",
                        "width": 1024,
                        "height": 1024,
                        "num_images": 1,
                        "photoReal": True,
                        "alchemy": True,
                    },
                    timeout=120.0,
                )

                response.raise_for_status()
                data = response.json()
                generation_id = data["sdGenerationJob"]["generationId"]
                image_url = await self._poll_leonardo_generation(client, generation_id)

                generation_time = time.time() - start_time

                params = {
                    "model": "leonardo_phoenix",
                    "photo_real": True,
                    "alchemy": True,
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
                headers={"Authorization": f"Bearer {self.leonardo_key}"},
            )

            data = response.json()

            if data["generations_by_pk"]["status"] == "COMPLETE":
                return data["generations_by_pk"]["generated_images"][0]["url"]

            await asyncio.sleep(2)
            attempt += 1

        raise TimeoutError("Leonardo generation timed out")

    async def generate_via_dall_e(
        self,
        request: FacialGenerationRequest,
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
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": "1024x1024",
                        "quality": "hd",
                        "style": "natural",
                    },
                    timeout=60.0,
                )

                response.raise_for_status()
                data = response.json()

                generation_time = time.time() - start_time
                image_url = data["data"][0]["url"]

                params = {
                    "model": "dall-e-3",
                    "quality": "hd",
                    "style": "natural",
                }

                return image_url, params, generation_time

            except Exception as e:
                raise Exception(f"DALL-E 3 generation failed: {str(e)}")

    async def generate_with_routing(
        self,
        request: FacialGenerationRequest,
    ) -> Tuple[str, FacialMetadata, float, ProviderType]:
        """
        Intelligent provider routing:
        1. Use specified provider if available
        2. Fall back to priority order
        3. Return image URL, metadata, cost, and provider used
        """

        if request.provider:
            providers_to_try = [self._resolve_provider(request.provider)]
        else:
            providers_to_try = self._default_provider_order()

        has_any_provider = bool(
            self.modal_endpoint_url
            or self.replicate_token
            or self.leonardo_key
            or self.openai_key
        )
        if not has_any_provider:
            image_url, params, gen_time = self._generate_local_placeholder(request)
            metadata = FacialMetadata(
                age=self._estimate_age_from_range(request.age_range),
                ethnicity=request.ethnicity or "diverse",
                aesthetic_style=request.aesthetic_style,
                dominant_features=[],
                quality_score=0.5,
                provider_used="modal_sdxl_lora",
                generation_params=params,
            )
            return image_url, metadata, 0.0, "modal_sdxl_lora"

        last_error = None

        for provider in providers_to_try:
            try:
                if not self._is_provider_available(provider):
                    continue

                handler = self._provider_handler(provider)
                image_url, params, gen_time = await handler(request)

                metadata = FacialMetadata(
                    age=self._estimate_age_from_range(request.age_range),
                    ethnicity=request.ethnicity or "diverse",
                    aesthetic_style=request.aesthetic_style,
                    dominant_features=[],
                    quality_score=0.85,
                    provider_used=provider,
                    generation_params=params,
                )

                cost = PROVIDER_PRICING.get(provider, 0.02)
                return image_url, metadata, cost, provider

            except Exception as e:
                last_error = e
                continue

        raise Exception(f"All providers failed. Last error: {str(last_error)}")

    def _estimate_age_from_range(self, age_range: str) -> int:
        """Estimate median age from range"""
        ranges = {
            "18-25": 22,
            "26-35": 30,
            "36-45": 40,
            "46+": 50,
        }
        return ranges.get(age_range, 30)


# Singleton instance
ai_provider_service = AIProviderService()
