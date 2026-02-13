from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime

# Provider types
ProviderType = Literal["modal_sdxl_lora", "replicate_sdxl", "midjourney", "leonardo", "dall_e_3"]

# Request schemas
class FacialGenerationRequest(BaseModel):
    """Request for generating avatar facial features"""
    age_range: Literal["18-25", "26-35", "36-45", "46+"] = Field(
        default="26-35",
        description="Age range for the avatar"
    )
    ethnicity: Optional[str] = Field(
        default="diverse",
        description="Ethnicity/appearance characteristics"
    )
    aesthetic_style: str = Field(
        ...,
        description="Aesthetic style (e.g., 'fitness', 'lifestyle', 'artistic', 'glamorous')"
    )
    gender: Literal["female", "male", "non-binary"] = Field(
        default="female",
        description="Gender presentation"
    )
    custom_prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt additions"
    )
    provider: Optional[ProviderType] = Field(
        default=None,
        description="Preferred AI provider (auto-selected if not specified)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "age_range": "26-35",
                "ethnicity": "latina",
                "aesthetic_style": "fitness",
                "gender": "female",
                "custom_prompt": "athletic build, confident smile"
            }
        }


class FacialMetadata(BaseModel):
    """Metadata extracted/generated for the face"""
    age: int = Field(..., ge=18, le=65, description="Estimated age")
    ethnicity: str
    aesthetic_style: str
    dominant_features: list[str] = Field(
        default_factory=list,
        description="Key facial features (e.g., 'high cheekbones', 'full lips')"
    )
    color_palette: Optional[dict] = Field(
        default=None,
        description="Dominant colors in the image"
    )
    quality_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Image quality score (0-1)"
    )
    provider_used: ProviderType
    generation_params: dict = Field(
        default_factory=dict,
        description="Parameters used for generation"
    )


class FacialGenerationResponse(BaseModel):
    """Response from facial generation"""
    success: bool
    avatar_id: Optional[UUID] = None
    image_url: str
    metadata: FacialMetadata
    cost_usd: float = Field(..., description="Cost of generation in USD")
    generation_time_seconds: float
    provider: ProviderType

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "avatar_id": "123e4567-e89b-12d3-a456-426614174000",
                "image_url": "https://r2.vixenbliss.com/avatars/base/abc123.jpg",
                "metadata": {
                    "age": 28,
                    "ethnicity": "latina",
                    "aesthetic_style": "fitness",
                    "dominant_features": ["athletic build", "confident expression"],
                    "quality_score": 0.92,
                    "provider_used": "modal_sdxl_lora",
                    "generation_params": {"steps": 30, "cfg_scale": 7.5}
                },
                "cost_usd": 0.015,
                "generation_time_seconds": 8.5,
                "provider": "modal_sdxl_lora"
            }
        }


# Avatar creation schema
class AvatarCreateRequest(BaseModel):
    """Request to create a new avatar"""
    name: str = Field(..., min_length=1, max_length=255)
    niche: str = Field(..., description="Target niche (e.g., 'fitness', 'lifestyle', 'fashion')")
    aesthetic_style: str
    facial_generation: FacialGenerationRequest
    lora_model_id: Optional[UUID] = Field(default=None, description="Optional preloaded LoRA model ID")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Valentina Fitness",
                "niche": "fitness",
                "aesthetic_style": "athletic_glamorous",
                "facial_generation": {
                    "age_range": "26-35",
                    "ethnicity": "latina",
                    "aesthetic_style": "fitness",
                    "gender": "female"
                }
            }
        }


class AvatarCreateWithLoRARequest(BaseModel):
    """Request to create avatar with pre-trained LoRA (skip training)"""
    name: str = Field(..., min_length=1, max_length=255)
    niche: str = Field(..., description="Target niche (e.g., 'fitness', 'lifestyle', 'fashion')")
    aesthetic_style: str
    lora_model_id: Optional[UUID] = Field(default=None, description="Catalog LoRA model ID")
    lora_weights_url: Optional[str] = Field(default=None, description="URL to LoRA weights file (.safetensors)")
    base_image_url: Optional[str] = Field(None, description="Optional reference image of the avatar")
    bio: Optional[str] = Field(None, description="Avatar biography/personality description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sofia Fitness",
                "niche": "fitness",
                "aesthetic_style": "athletic_natural",
                "lora_model_id": "ostris/flux-dev-lora-trainer:abc123",
                "lora_weights_url": "https://replicate.delivery/pbxt/lora_weights.safetensors",
                "base_image_url": "https://r2.vixenbliss.com/avatars/sofia-reference.jpg",
                "bio": "Fitness enthusiast and wellness coach from Miami"
            }
        }


class AvatarResponse(BaseModel):
    """Avatar details response"""
    id: UUID
    user_id: UUID
    name: str
    stage: str
    base_image_url: Optional[str]
    lora_model_id: Optional[str]
    niche: Optional[str]
    aesthetic_style: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: dict = Field(default_factory=dict, validation_alias="meta_data")

    class Config:
        from_attributes = True
