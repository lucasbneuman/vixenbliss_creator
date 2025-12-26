from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class DatasetGenerationRequest(BaseModel):
    """Request to generate training dataset for LoRA"""
    avatar_id: UUID
    num_images: int = Field(default=50, ge=20, le=100, description="Number of images to generate")
    variation_types: List[str] = Field(
        default_factory=lambda: ["angles", "lighting", "expressions", "poses"],
        description="Types of variations to generate"
    )
    use_base_image: bool = Field(
        default=True,
        description="Use avatar's base image as seed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "avatar_id": "123e4567-e89b-12d3-a456-426614174000",
                "num_images": 50,
                "variation_types": ["angles", "lighting", "expressions"],
                "use_base_image": True
            }
        }


class DatasetImage(BaseModel):
    """Individual image in the dataset"""
    url: str
    variation_type: str
    prompt_used: str
    quality_score: float = Field(..., ge=0.0, le=1.0)
    clip_similarity: Optional[float] = Field(None, ge=0.0, le=1.0)


class DatasetGenerationResponse(BaseModel):
    """Response from dataset generation"""
    success: bool
    avatar_id: UUID
    batch_id: str
    total_images: int
    images: List[DatasetImage]
    total_cost_usd: float
    generation_time_seconds: float
    dataset_zip_url: Optional[str] = None
    average_quality_score: float

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "avatar_id": "123e4567-e89b-12d3-a456-426614174000",
                "batch_id": "batch_abc123",
                "total_images": 50,
                "images": [],
                "total_cost_usd": 0.75,
                "generation_time_seconds": 240.5,
                "dataset_zip_url": "https://r2.vixenbliss.com/datasets/batch_abc123.zip",
                "average_quality_score": 0.87
            }
        }


class LoRATrainingRequest(BaseModel):
    """Request to start LoRA training"""
    avatar_id: UUID
    dataset_batch_id: str
    training_steps: int = Field(default=1500, ge=500, le=3000)
    learning_rate: float = Field(default=1e-4, gt=0, le=1e-2)
    lora_rank: int = Field(default=128, ge=64, le=256)
    use_auto_captions: bool = Field(default=True, description="Auto-generate captions for images")

    class Config:
        json_schema_extra = {
            "example": {
                "avatar_id": "123e4567-e89b-12d3-a456-426614174000",
                "dataset_batch_id": "batch_abc123",
                "training_steps": 1500,
                "learning_rate": 0.0001,
                "lora_rank": 128,
                "use_auto_captions": True
            }
        }


class LoRATrainingResponse(BaseModel):
    """Response from LoRA training initiation"""
    success: bool
    avatar_id: UUID
    training_job_id: str
    estimated_time_minutes: int
    cost_estimate_usd: float
    status: str
    weights_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "avatar_id": "123e4567-e89b-12d3-a456-426614174000",
                "training_job_id": "train_xyz789",
                "estimated_time_minutes": 25,
                "cost_estimate_usd": 2.50,
                "status": "queued",
                "weights_url": None
            }
        }


class LoRATrainingStatus(BaseModel):
    """Status of LoRA training job"""
    training_job_id: str
    status: str  # queued, running, completed, failed
    progress_percentage: float
    current_step: int
    total_steps: int
    estimated_time_remaining_minutes: Optional[int]
    loss: Optional[float]
    weights_url: Optional[str]
    error_message: Optional[str]
