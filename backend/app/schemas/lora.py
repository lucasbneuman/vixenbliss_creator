from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DatasetImage(BaseModel):
    """Single image metadata in a generated LoRA training dataset."""

    url: str
    variation_type: str
    prompt_used: str
    quality_score: float = Field(..., ge=0.0, le=1.0)
    clip_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class DatasetGenerationRequest(BaseModel):
    """Request to generate training dataset for LoRA."""

    avatar_id: UUID
    num_images: int = Field(default=50, ge=10, le=200)
    variation_types: list[str] = Field(
        default_factory=lambda: ["angles", "lighting", "expressions", "poses"]
    )


class DatasetGenerationResponse(BaseModel):
    """Response for dataset generation."""

    success: bool
    avatar_id: UUID
    batch_id: str
    total_images: int
    images: list[DatasetImage] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    generation_time_seconds: float = 0.0
    dataset_zip_url: Optional[str] = None
    average_quality_score: float = 0.0


class LoRATrainingRequest(BaseModel):
    """Request to start LoRA training."""

    avatar_id: UUID
    dataset_batch_id: str
    training_steps: int = Field(default=2000, ge=500, le=5000)
    learning_rate: float = Field(default=0.0001, gt=0, le=0.01)
    lora_rank: int = Field(default=128, ge=64, le=256)
    use_auto_captions: bool = True


class LoRATrainingResponse(BaseModel):
    """Response when LoRA training task is queued."""

    success: bool
    avatar_id: UUID
    training_job_id: str
    estimated_time_minutes: int
    cost_estimate_usd: float
    status: str
    weights_url: Optional[str] = None


class LoRATrainingStatus(BaseModel):
    """Status of a LoRA training job."""

    training_job_id: str
    status: str
    progress_percentage: float = 0.0
    current_step: int = 0
    total_steps: int = 0
    estimated_time_remaining_minutes: Optional[int] = None
    loss: Optional[float] = None
    weights_url: Optional[str] = None
    error_message: Optional[str] = None


class LoRAModelCreateRequest(BaseModel):
    """Create LoRA model record from an existing URL."""

    name: str = Field(..., min_length=1, max_length=255)
    lora_weights_url: str
    description: Optional[str] = None
    base_model: Optional[str] = None
    preview_image_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    meta_data: dict[str, Any] = Field(default_factory=dict)


class LoRAModelResponse(BaseModel):
    """LoRA model response."""

    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    base_model: Optional[str] = None
    lora_weights_url: str
    preview_image_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True
    meta_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
