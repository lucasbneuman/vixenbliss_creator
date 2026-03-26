from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_utc_datetime(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() == timezone.utc.utcoffset(value)


class IdentitySchemaVersion(str, Enum):
    V1 = "1.0.0"


class TechnicalSheetSchemaVersion(str, Enum):
    V1 = "1.0.0"


class IdentityStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class PipelineState(str, Enum):
    DRAFT = "draft"
    IDENTITY_CREATED = "identity_created"
    BASE_IMAGES_GENERATED = "base_images_generated"
    BASE_IMAGES_REGISTERED = "base_images_registered"
    DATASET_READY = "dataset_ready"
    LORA_TRAINING_PENDING = "lora_training_pending"
    LORA_TRAINING_RUNNING = "lora_training_running"
    LORA_TRAINED = "lora_trained"
    LORA_VALIDATED = "lora_validated"
    VIDEO_READY_FOR_FUTURE_INTEGRATION = "video_ready_for_future_integration"


class Vertical(str, Enum):
    ADULT_ENTERTAINMENT = "adult_entertainment"
    LIFESTYLE = "lifestyle"
    PERFORMANCE = "performance"
    EXPERIMENTAL = "experimental"


class AllowedContentMode(str, Enum):
    SFW = "sfw"
    SENSUAL = "sensual"
    NSFW = "nsfw"


class DatasetStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    REJECTED = "rejected"


class VoiceTone(str, Enum):
    FORMAL = "formal"
    INFORMAL = "informal"
    PLAYFUL = "playful"
    AUTHORITATIVE = "authoritative"
    SEDUCTIVE = "seductive"


class AudienceRole(str, Enum):
    ASPIRATIONAL = "aspirational"
    CONFIDANT = "confidant"
    PERFORMER = "performer"
    FANTASY_GUIDE = "fantasy_guide"


class BoundarySeverity(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class FormalityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IntensityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TechnicalSheetBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, use_enum_values=True)


class IdentityCore(TechnicalSheetBaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    fictional_age_years: int = Field(ge=18, le=99)
    locale: str = Field(min_length=2, max_length=32)
    primary_language: str = Field(min_length=2, max_length=32)
    secondary_languages: list[str] = Field(default_factory=list, max_length=5)
    tagline: str = Field(min_length=8, max_length=160)


class VisualProfile(TechnicalSheetBaseModel):
    archetype: str = Field(min_length=3, max_length=80)
    body_type: str = Field(min_length=3, max_length=60)
    skin_tone: str = Field(min_length=3, max_length=40)
    eye_color: str = Field(min_length=3, max_length=30)
    hair_color: str = Field(min_length=3, max_length=30)
    hair_style: str = Field(min_length=3, max_length=60)
    dominant_features: list[str] = Field(min_length=2, max_length=8)
    wardrobe_styles: list[str] = Field(min_length=1, max_length=8)
    visual_must_haves: list[str] = Field(min_length=1, max_length=8)
    visual_never_do: list[str] = Field(min_length=1, max_length=8)


class PersonalityAxes(TechnicalSheetBaseModel):
    formality: FormalityLevel
    warmth: IntensityLevel
    dominance: IntensityLevel
    provocation: IntensityLevel
    accessibility: IntensityLevel


class PersonalityProfile(TechnicalSheetBaseModel):
    voice_tone: VoiceTone
    primary_traits: list[str] = Field(min_length=2, max_length=8)
    secondary_traits: list[str] = Field(default_factory=list, max_length=8)
    interaction_style: str = Field(min_length=8, max_length=160)
    axes: PersonalityAxes


class NarrativeProfile(TechnicalSheetBaseModel):
    archetype_summary: str = Field(min_length=24, max_length=240)
    origin_story: str = Field(min_length=24, max_length=320)
    motivations: list[str] = Field(min_length=2, max_length=8)
    interests: list[str] = Field(min_length=2, max_length=10)
    audience_role: AudienceRole
    conversational_hooks: list[str] = Field(min_length=2, max_length=8)


class OperationalBoundary(TechnicalSheetBaseModel):
    code: str = Field(pattern=r"^[a-z0-9_]+$", min_length=3, max_length=48)
    label: str = Field(min_length=3, max_length=80)
    severity: BoundarySeverity
    rationale: str = Field(min_length=8, max_length=160)


class OperationalLimits(TechnicalSheetBaseModel):
    allowed_content_modes: list[AllowedContentMode] = Field(min_length=1, max_length=3)
    hard_limits: list[OperationalBoundary] = Field(default_factory=list, max_length=12)
    soft_limits: list[OperationalBoundary] = Field(default_factory=list, max_length=12)
    escalation_triggers: list[str] = Field(default_factory=list, max_length=8)


class System5Slots(TechnicalSheetBaseModel):
    persona_summary: str = Field(min_length=24, max_length=240)
    greeting_style: str = Field(min_length=8, max_length=120)
    reply_style_keywords: list[str] = Field(min_length=2, max_length=8)
    memory_tags: list[str] = Field(min_length=2, max_length=10)
    prohibited_topics: list[str] = Field(default_factory=list, max_length=12)
    upsell_style: str = Field(min_length=8, max_length=120)


class TraceabilityMetadata(TechnicalSheetBaseModel):
    source_issue_id: str = Field(pattern=r"^[A-Z]+-\d+$")
    source_epic_id: str = Field(pattern=r"^[A-Z]+-\d+$")
    contract_owner: str = Field(min_length=3, max_length=80)
    future_systems_ready: list[Literal["system_2", "system_5"]] = Field(min_length=1, max_length=2)
    last_reviewed_at: datetime


class TechnicalSheet(TechnicalSheetBaseModel):
    schema_version: TechnicalSheetSchemaVersion = TechnicalSheetSchemaVersion.V1
    identity_core: IdentityCore
    visual_profile: VisualProfile
    personality_profile: PersonalityProfile
    narrative_profile: NarrativeProfile
    operational_limits: OperationalLimits
    system5_slots: System5Slots
    traceability: TraceabilityMetadata


class Identity(TechnicalSheetBaseModel):
    schema_version: IdentitySchemaVersion = IdentitySchemaVersion.V1
    id: UUID
    alias: str = Field(pattern=r"^[a-z0-9]+(?:_[a-z0-9]+)*$", min_length=3, max_length=40)
    status: IdentityStatus = IdentityStatus.DRAFT
    pipeline_state: PipelineState = PipelineState.DRAFT
    vertical: Vertical
    allowed_content_modes: list[AllowedContentMode] = Field(min_length=1, max_length=3)
    reference_face_image_url: HttpUrl | None = None
    base_image_urls: list[HttpUrl] = Field(default_factory=list, max_length=12)
    dataset_storage_path: str | None = Field(default=None, min_length=3, max_length=255)
    dataset_status: DatasetStatus = DatasetStatus.NOT_STARTED
    base_model_id: str | None = Field(default=None, min_length=3, max_length=120)
    lora_model_path: str | None = Field(default=None, min_length=3, max_length=255)
    lora_version: str | None = Field(default=None, min_length=1, max_length=40)
    technical_sheet_json: TechnicalSheet
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_consistency(self) -> "Identity":
        top_level_modes = self.allowed_content_modes
        sheet_modes = self.technical_sheet_json.operational_limits.allowed_content_modes
        if len(top_level_modes) != len(set(top_level_modes)):
            raise ValueError("allowed_content_modes must not contain duplicates")
        if len(sheet_modes) != len(set(sheet_modes)):
            raise ValueError(
                "technical_sheet_json.operational_limits.allowed_content_modes must not contain duplicates"
            )
        if top_level_modes != sheet_modes:
            raise ValueError("allowed_content_modes must match technical_sheet_json.operational_limits.allowed_content_modes")
        if not is_utc_datetime(self.created_at):
            raise ValueError("created_at must be a UTC datetime")
        if not is_utc_datetime(self.updated_at):
            raise ValueError("updated_at must be a UTC datetime")
        if not is_utc_datetime(self.technical_sheet_json.traceability.last_reviewed_at):
            raise ValueError("traceability.last_reviewed_at must be a UTC datetime")
        if self.technical_sheet_json.traceability.last_reviewed_at > self.updated_at:
            raise ValueError("traceability.last_reviewed_at cannot be later than updated_at")
        if self.created_at > self.updated_at:
            raise ValueError("created_at cannot be later than updated_at")
        if self.pipeline_state == PipelineState.DRAFT and self.status != IdentityStatus.DRAFT:
            raise ValueError("draft pipeline_state requires draft status")
        return self
