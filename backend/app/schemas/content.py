"""
Content Generation Schemas
Pydantic schemas for content production API
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ContentGenerationRequest(BaseModel):
    """Request for single image generation"""
    avatar_id: str
    template_id: Optional[str] = None
    custom_prompt: Optional[str] = None
    platform: str = "instagram"
    tier: Optional[str] = None


class BatchGenerationRequest(BaseModel):
    """Request for batch content generation"""
    avatar_id: str
    num_pieces: int = Field(default=50, ge=1, le=100)
    platform: str = "instagram"
    tier_distribution: Optional[Dict[str, float]] = None
    include_hooks: bool = True
    safety_check: bool = True
    upload_to_storage: bool = True


class HookGenerationRequest(BaseModel):
    """Request for hook generation"""
    avatar_id: str
    content_type: str
    platform: str = "instagram"
    num_variations: int = Field(default=5, ge=1, le=10)


class SafetyCheckRequest(BaseModel):
    """Request for content safety check"""
    image_url: str
    prompt: Optional[str] = None


class TemplateListResponse(BaseModel):
    """Response for template list"""
    templates: List[Dict[str, Any]]
    total: int
    categories: List[str]


class ContentPieceResponse(BaseModel):
    """Response for single content piece"""
    id: str
    avatar_id: str
    content_type: str
    access_tier: str
    url: str
    hook_text: Optional[str] = None
    safety_rating: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class BatchGenerationResponse(BaseModel):
    """Response for batch generation"""
    success: bool
    avatar_id: str
    total_pieces: int
    content_pieces: List[ContentPieceResponse]
    statistics: Dict[str, Any]
    config: Dict[str, Any]


class HookGenerationResponse(BaseModel):
    """Response for hook generation"""
    hooks: List[Dict[str, Any]]
    platform: str
    content_type: str


class SafetyCheckResponse(BaseModel):
    """Response for safety check"""
    rating: str
    access_tier: Optional[str] = None
    scores: Dict[str, float]
    flagged_categories: List[str]
    safe: bool
    reason: Optional[str] = None
