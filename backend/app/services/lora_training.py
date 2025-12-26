"""
LoRA Training Service
Handles LoRA fine-tuning via Replicate/Google Colab
"""

import os
import time
import httpx
import replicate
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.avatar import Avatar


class LoRATrainingService:
    """Service for LoRA model training"""

    def __init__(self):
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        self.colab_webhook_url = os.getenv("COLAB_WEBHOOK_URL")  # Optional: for Colab integration

    async def train_lora_replicate(
        self,
        avatar_id: str,
        dataset_zip_url: str,
        training_steps: int = 1500,
        learning_rate: float = 1e-4,
        lora_rank: int = 128
    ) -> Dict[str, Any]:
        """
        Train LoRA using Replicate's training API

        Uses: ostris/flux-dev-lora-trainer or similar model
        """

        try:
            training = replicate.trainings.create(
                version="ostris/flux-dev-lora-trainer:e440909d3512c31646ee2e0c7d6f6f4923224863a6a10c494606e79fb5844497",
                input={
                    "input_images": dataset_zip_url,
                    "steps": training_steps,
                    "lora_rank": lora_rank,
                    "learning_rate": learning_rate,
                    "trigger_word": f"TOK_{avatar_id[:8]}",  # Unique trigger word
                    "batch_size": 1,
                    "resolution": "1024,1024",
                    "autocaption": True
                },
                destination=f"vixenbliss/avatar-{avatar_id[:8]}"
            )

            return {
                "training_id": training.id,
                "status": training.status,
                "created_at": str(training.created_at),
                "provider": "replicate"
            }

        except Exception as e:
            raise Exception(f"Replicate training failed: {str(e)}")

    async def train_lora_colab(
        self,
        avatar_id: str,
        dataset_zip_url: str,
        training_steps: int = 1500,
        learning_rate: float = 1e-4,
        lora_rank: int = 128
    ) -> Dict[str, Any]:
        """
        Train LoRA using Google Colab Pro (via webhook/API)

        Assumes a Colab notebook is running with Kohya_ss and webhook endpoint
        """

        if not self.colab_webhook_url:
            raise ValueError("Colab webhook URL not configured")

        payload = {
            "avatar_id": avatar_id,
            "dataset_url": dataset_zip_url,
            "training_config": {
                "steps": training_steps,
                "learning_rate": learning_rate,
                "lora_rank": lora_rank,
                "batch_size": 1,
                "gradient_accumulation_steps": 4,
                "mixed_precision": "fp16",
                "network_dim": lora_rank,
                "network_alpha": lora_rank // 2
            }
        }

        async with httpx.AsyncClient(timeout=600.0) as client:
            try:
                response = await client.post(
                    self.colab_webhook_url,
                    json=payload
                )

                response.raise_for_status()
                result = response.json()

                return {
                    "training_id": result.get("job_id"),
                    "status": "started",
                    "provider": "colab",
                    "colab_url": result.get("colab_url")
                }

            except Exception as e:
                raise Exception(f"Colab training failed: {str(e)}")

    async def get_training_status_replicate(self, training_id: str) -> Dict[str, Any]:
        """Get training status from Replicate"""

        try:
            training = replicate.trainings.get(training_id)

            return {
                "status": training.status,
                "progress": self._estimate_progress(training),
                "logs": training.logs if hasattr(training, 'logs') else None,
                "output": training.output if training.status == "succeeded" else None,
                "error": training.error if training.status == "failed" else None
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _estimate_progress(self, training: Any) -> float:
        """Estimate training progress percentage"""

        if training.status == "succeeded":
            return 100.0
        elif training.status == "failed" or training.status == "canceled":
            return 0.0
        elif training.status == "processing":
            # Estimate based on typical training time (25 minutes)
            created_at = training.created_at
            elapsed_minutes = (time.time() - created_at.timestamp()) / 60
            return min(elapsed_minutes / 25.0 * 100, 95.0)
        else:
            return 0.0

    async def finalize_training(
        self,
        db: Session,
        avatar_id: str,
        weights_url: str,
        training_metadata: Dict[str, Any]
    ) -> Avatar:
        """Update avatar with trained LoRA weights"""

        from uuid import UUID

        avatar = db.query(Avatar).filter(Avatar.id == UUID(avatar_id)).first()

        if not avatar:
            raise ValueError(f"Avatar {avatar_id} not found")

        avatar.lora_weights_url = weights_url
        avatar.lora_model_id = training_metadata.get("model_id")
        avatar.stage = "lora_trained"

        avatar.metadata = avatar.metadata or {}
        avatar.metadata["lora_training"] = {
            "weights_url": weights_url,
            "training_steps": training_metadata.get("steps"),
            "final_loss": training_metadata.get("final_loss"),
            "completed_at": str(time.time()),
            "provider": training_metadata.get("provider")
        }

        db.commit()
        db.refresh(avatar)

        return avatar


# Singleton instance
lora_training_service = LoRATrainingService()
