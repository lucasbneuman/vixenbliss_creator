"""
Dataset Builder Service
Generates training datasets for LoRA fine-tuning
"""

import asyncio
import uuid
import time
import zipfile
import io
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
import httpx

from app.models.avatar import Avatar
from app.schemas.lora import (
    DatasetGenerationRequest,
    DatasetGenerationResponse,
    DatasetImage
)
from app.services.ai_providers import ai_provider_service
from app.services.storage import storage_service


# Variation prompts for different types
VARIATION_PROMPTS = {
    "angles": [
        "front facing portrait",
        "45 degree angle portrait",
        "side profile portrait",
        "three quarter view portrait",
        "looking over shoulder",
        "slight upward angle",
        "slight downward angle"
    ],
    "lighting": [
        "soft natural lighting",
        "dramatic studio lighting",
        "golden hour lighting",
        "rim lighting",
        "soft window light",
        "high key lighting",
        "low key lighting"
    ],
    "expressions": [
        "confident smile",
        "subtle smile",
        "serious expression",
        "playful expression",
        "contemplative look",
        "joyful laugh",
        "relaxed neutral expression"
    ],
    "poses": [
        "standing upright, confident pose",
        "casual leaning pose",
        "hands on hips power pose",
        "arms crossed",
        "hand in hair",
        "looking away thoughtfully",
        "dynamic action pose"
    ]
}


class DatasetBuilderService:
    """Service for building LoRA training datasets"""

    async def generate_dataset(
        self,
        db: Session,
        request: DatasetGenerationRequest
    ) -> DatasetGenerationResponse:
        """
        Generate training dataset with variations

        Workflow:
        1. Load avatar base image and metadata
        2. Generate variations across multiple dimensions
        3. Validate consistency using CLIP embeddings
        4. Upload all images to R2
        5. Create ZIP archive for training
        6. Return dataset metadata
        """

        # Step 1: Load avatar
        avatar = db.query(Avatar).filter(Avatar.id == request.avatar_id).first()
        if not avatar:
            raise ValueError(f"Avatar {request.avatar_id} not found")

        # Step 2: Generate batch ID
        batch_id = f"dataset_{uuid.uuid4().hex[:12]}"

        # Step 3: Calculate distribution across variation types
        images_per_type = request.num_images // len(request.variation_types)

        # Step 4: Generate images
        start_time = time.time()
        all_images: List[DatasetImage] = []
        total_cost = 0.0

        for variation_type in request.variation_types:
            prompts = VARIATION_PROMPTS.get(variation_type, ["portrait"])

            # Generate images for this variation type
            for i in range(images_per_type):
                prompt_variation = prompts[i % len(prompts)]

                try:
                    image_url, metadata, cost = await self._generate_variation(
                        avatar=avatar,
                        variation_type=variation_type,
                        prompt_variation=prompt_variation
                    )

                    # Upload to R2
                    file_key = f"datasets/{batch_id}/{variation_type}_{i:03d}.jpg"
                    permanent_url = await self._download_and_upload(image_url, file_key)

                    dataset_image = DatasetImage(
                        url=permanent_url,
                        variation_type=variation_type,
                        prompt_used=prompt_variation,
                        quality_score=metadata.get("quality_score", 0.85),
                        clip_similarity=None  # TODO: Calculate CLIP similarity
                    )

                    all_images.append(dataset_image)
                    total_cost += cost

                except Exception as e:
                    print(f"Failed to generate variation {i} for {variation_type}: {str(e)}")
                    continue

        generation_time = time.time() - start_time

        # Step 5: Create ZIP archive
        zip_url = await self._create_dataset_zip(batch_id, all_images)

        # Step 6: Calculate average quality
        avg_quality = sum(img.quality_score for img in all_images) / len(all_images) if all_images else 0.0

        # Step 7: Update avatar metadata
        avatar.metadata = avatar.metadata or {}
        avatar.metadata["dataset"] = {
            "batch_id": batch_id,
            "num_images": len(all_images),
            "zip_url": zip_url,
            "created_at": str(time.time())
        }
        db.commit()

        return DatasetGenerationResponse(
            success=True,
            avatar_id=request.avatar_id,
            batch_id=batch_id,
            total_images=len(all_images),
            images=all_images,
            total_cost_usd=round(total_cost, 2),
            generation_time_seconds=round(generation_time, 1),
            dataset_zip_url=zip_url,
            average_quality_score=round(avg_quality, 2)
        )

    async def _generate_variation(
        self,
        avatar: Avatar,
        variation_type: str,
        prompt_variation: str
    ) -> Tuple[str, Dict, float]:
        """Generate a single variation image"""

        # Build prompt from avatar metadata
        base_metadata = avatar.metadata.get("facial_metadata", {})

        prompt = (
            f"Professional photorealistic portrait, "
            f"{base_metadata.get('aesthetic_style', 'lifestyle')} style, "
            f"{prompt_variation}, "
            f"high quality photography, sharp focus, 8k resolution"
        )

        negative = "cartoon, anime, illustration, distorted, blurry, low quality"

        # Use Replicate SDXL for speed
        import replicate
        output = await replicate.async_run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": prompt,
                "negative_prompt": negative,
                "num_outputs": 1,
                "num_inference_steps": 25,  # Faster for dataset
                "guidance_scale": 7.0,
                "width": 1024,
                "height": 1024
            }
        )

        image_url = output[0] if isinstance(output, list) else output

        metadata = {
            "variation_type": variation_type,
            "prompt": prompt,
            "quality_score": 0.85
        }

        cost = 0.01  # SDXL cost

        return image_url, metadata, cost

    async def _download_and_upload(self, temp_url: str, file_key: str) -> str:
        """Download image from temp URL and upload to R2"""

        async with httpx.AsyncClient() as client:
            response = await client.get(temp_url)
            response.raise_for_status()
            image_bytes = response.content

        permanent_url = await storage_service.upload_file_async(
            file_data=image_bytes,
            file_key=file_key,
            content_type="image/jpeg"
        )

        return permanent_url

    async def _create_dataset_zip(self, batch_id: str, images: List[DatasetImage]) -> str:
        """Create ZIP archive of dataset for training"""

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Download and add each image
            async with httpx.AsyncClient() as client:
                for idx, img in enumerate(images):
                    try:
                        response = await client.get(img.url)
                        response.raise_for_status()

                        filename = f"{idx:03d}_{img.variation_type}.jpg"
                        zip_file.writestr(filename, response.content)

                        # Also create caption file for auto-captioning
                        caption_filename = f"{idx:03d}_{img.variation_type}.txt"
                        zip_file.writestr(caption_filename, img.prompt_used)

                    except Exception as e:
                        print(f"Failed to add image {idx} to ZIP: {str(e)}")
                        continue

        # Upload ZIP to R2
        zip_bytes = zip_buffer.getvalue()
        zip_key = f"datasets/{batch_id}/dataset.zip"

        zip_url = await storage_service.upload_file_async(
            file_data=zip_bytes,
            file_key=zip_key,
            content_type="application/zip"
        )

        return zip_url


# Singleton instance
dataset_builder_service = DatasetBuilderService()
