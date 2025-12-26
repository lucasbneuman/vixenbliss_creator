"""
LoRA Inference Engine
Generates images using trained LoRA weights via Replicate API
"""

import os
import time
import asyncio
import replicate
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.avatar import Avatar
from app.models.content_piece import ContentPiece


class LoRAInferenceEngine:
    """Service for generating images with custom LoRA weights"""

    def __init__(self):
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        self.default_model = "black-forest-labs/flux-1.1-pro"

    async def generate_image_with_lora(
        self,
        avatar: Avatar,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_inference_steps: int = 28,
        guidance_scale: float = 3.5,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate single image with LoRA weights

        Args:
            avatar: Avatar with trained LoRA weights
            prompt: Generation prompt
            negative_prompt: Things to avoid
            num_inference_steps: Number of denoising steps (20-50)
            guidance_scale: How closely to follow prompt (1.0-10.0)
            width: Image width (recommended: 1024)
            height: Image height (recommended: 1024)
            seed: Random seed for reproducibility

        Returns:
            Dict with image_url, generation_time, parameters
        """

        if not avatar.lora_weights_url:
            raise ValueError(f"Avatar {avatar.id} has no LoRA weights trained")

        # Build trigger word for LoRA
        trigger_word = f"TOK_{str(avatar.id)[:8]}"

        # Inject trigger word into prompt
        enhanced_prompt = f"{trigger_word}, {prompt}"

        # Default negative prompt
        if not negative_prompt:
            negative_prompt = (
                "cartoon, anime, 3d render, illustration, painting, drawing, "
                "unrealistic, distorted, blurry, low quality, watermark, text, "
                "multiple people, crowd, duplicate, deformed, ugly"
            )

        start_time = time.time()

        try:
            # Use Flux with custom LoRA weights
            input_params = {
                "prompt": enhanced_prompt,
                "negative_prompt": negative_prompt,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "width": width,
                "height": height,
                "output_format": "jpg",
                "output_quality": 90,
                "lora_weights": avatar.lora_weights_url,
                "lora_scale": 0.8  # LoRA influence (0.0-1.0)
            }

            if seed is not None:
                input_params["seed"] = seed

            output = await replicate.async_run(
                self.default_model,
                input=input_params
            )

            generation_time = time.time() - start_time

            # Handle output (URL or file)
            if isinstance(output, list):
                image_url = output[0]
            elif hasattr(output, 'url'):
                image_url = output.url
            else:
                image_url = str(output)

            return {
                "image_url": image_url,
                "generation_time": generation_time,
                "parameters": {
                    "prompt": enhanced_prompt,
                    "negative_prompt": negative_prompt,
                    "steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "resolution": f"{width}x{height}",
                    "lora_weights": avatar.lora_weights_url,
                    "lora_scale": 0.8,
                    "seed": seed
                },
                "cost": 0.01  # $0.01 per image
            }

        except Exception as e:
            raise Exception(f"LoRA inference failed: {str(e)}")

    async def batch_generate_images(
        self,
        db: Session,
        avatar: Avatar,
        prompts: List[str],
        negative_prompt: Optional[str] = None,
        batch_config: Optional[Dict[str, Any]] = None
    ) -> List[ContentPiece]:
        """
        Generate multiple images in batch (for 50 content pieces)

        Args:
            db: Database session
            avatar: Avatar with trained LoRA weights
            prompts: List of prompts (one per image)
            negative_prompt: Shared negative prompt
            batch_config: Override generation parameters

        Returns:
            List of ContentPiece objects (not yet uploaded to R2)
        """

        config = batch_config or {}
        num_inference_steps = config.get("num_inference_steps", 28)
        guidance_scale = config.get("guidance_scale", 3.5)
        width = config.get("width", 1024)
        height = config.get("height", 1024)

        content_pieces = []
        tasks = []

        # Create async tasks for parallel generation
        for idx, prompt in enumerate(prompts):
            task = self.generate_image_with_lora(
                avatar=avatar,
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                seed=42 + idx  # Reproducible seeds
            )
            tasks.append(task)

        # Execute batch generation (limit concurrency to avoid rate limits)
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent generations

        async def generate_with_limit(task):
            async with semaphore:
                return await task

        results = await asyncio.gather(
            *[generate_with_limit(task) for task in tasks],
            return_exceptions=True
        )

        # Process results and create ContentPiece objects
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Generation {idx} failed: {str(result)}")
                continue

            # Create ContentPiece (temporary URL, will be replaced after R2 upload)
            content_piece = ContentPiece(
                avatar_id=avatar.id,
                content_type="image",
                access_tier="capa1",  # Default tier
                url=result["image_url"],  # Temporary Replicate URL
                metadata={
                    "generation_params": result["parameters"],
                    "generation_time": result["generation_time"],
                    "cost": result["cost"],
                    "prompt_index": idx,
                    "batch_generation": True
                }
            )

            content_pieces.append(content_piece)

        return content_pieces

    async def generate_with_template(
        self,
        avatar: Avatar,
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate image using a template from template_library

        Args:
            avatar: Avatar with LoRA weights
            template: Template dict with prompt_template, lighting, angle, etc.

        Returns:
            Generation result
        """

        # Extract avatar personality for prompt enhancement
        personality = avatar.metadata.get("personality", {})
        niche = avatar.niche or "lifestyle"
        aesthetic = avatar.aesthetic_style or "natural"

        # Build full prompt from template
        base_prompt = template["prompt_template"]

        # Add context
        full_prompt = (
            f"{base_prompt}, "
            f"{template.get('lighting', 'natural lighting')}, "
            f"{template.get('angle', 'medium shot')}, "
            f"{aesthetic} aesthetic, "
            f"{template.get('pose_description', 'confident pose')}"
        )

        # Generate
        return await self.generate_image_with_lora(
            avatar=avatar,
            prompt=full_prompt,
            negative_prompt=template.get("negative_prompt")
        )

    def estimate_batch_cost(self, num_images: int) -> float:
        """Estimate total cost for batch generation"""
        return num_images * 0.01  # $0.01 per image

    def estimate_batch_time(self, num_images: int, concurrent_limit: int = 5) -> float:
        """Estimate total time for batch generation (in seconds)"""
        avg_time_per_image = 8.0  # seconds
        batches = (num_images + concurrent_limit - 1) // concurrent_limit
        return batches * avg_time_per_image


# Singleton instance
lora_inference_engine = LoRAInferenceEngine()
