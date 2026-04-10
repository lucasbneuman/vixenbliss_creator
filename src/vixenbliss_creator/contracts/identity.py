from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import Field, HttpUrl, model_validator

from .common import ContractBaseModel, is_utc_datetime, utc_now


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


class CreationCategory(str, Enum):
    ADULT_CREATOR = "adult_creator"
    LIFESTYLE_PREMIUM = "lifestyle_premium"
    PERFORMANCE_ARTIST = "performance_artist"
    EXPERIMENTAL_MUSE = "experimental_muse"


class IdentityStyle(str, Enum):
    PREMIUM = "premium"
    CASUAL = "casual"
    GLAM = "glam"
    EDITORIAL = "editorial"
    ALTERNATIVE = "alternative"


class ArchetypeCode(str, Enum):
    GIRL_NEXT_DOOR = "girl_next_door"
    DOMINANT_QUEEN = "dominant_queen"
    PLAYFUL_TEASE = "playful_tease"
    LUXURY_MUSE = "luxury_muse"
    REBEL_ALTERNATIVE = "rebel_alternative"


class TraitScale(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class SpeechStyle(str, Enum):
    CASUAL = "casual"
    REFINED = "refined"
    DIRECT = "direct"
    PLAYFUL = "playful"
    GLAM = "glam"


class MessageLength(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class EmojiUsage(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class PunctuationStyle(str, Enum):
    SOFT = "soft"
    EXPRESSIVE = "expressive"
    POLISHED = "polished"
    MINIMAL = "minimal"


class FanRelationshipStyle(str, Enum):
    CLOSE_CONFIDANT = "close_confidant"
    CURATED_DISTANCE = "curated_distance"
    ASPIRATIONAL_MUSE = "aspirational_muse"
    COMMANDING_PRESENCE = "commanding_presence"


class AttentionStrategy(str, Enum):
    REACTIVE = "reactive"
    BALANCED = "balanced"
    PROACTIVE = "proactive"
    EXCLUSIVE = "exclusive"


class ResponseEnergy(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class JealousyPlayLevel(str, Enum):
    NONE = "none"
    LIGHT = "light"
    MODERATE = "moderate"


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


class FieldOrigin(str, Enum):
    MANUAL = "manual"
    INFERRED = "inferred"
    DEFAULTED = "defaulted"
    DERIVED = "derived"


class TechnicalSheetBaseModel(ContractBaseModel):
    pass


class IdentityCore(TechnicalSheetBaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    fictional_age_years: int = Field(ge=18, le=99)
    locale: str = Field(min_length=2, max_length=32)
    primary_language: str = Field(min_length=2, max_length=32)
    secondary_languages: list[str] = Field(default_factory=list, max_length=5)
    tagline: str = Field(min_length=8, max_length=160)


class IdentityMetadata(TechnicalSheetBaseModel):
    avatar_id: str | None = Field(default=None, min_length=3, max_length=80)
    category: CreationCategory
    vertical: Vertical
    style: IdentityStyle
    occupation_or_content_basis: str = Field(min_length=3, max_length=80)


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
    dominance: TraitScale
    warmth: TraitScale
    playfulness: TraitScale
    mystery: TraitScale
    flirtiness: TraitScale
    intelligence: TraitScale
    sarcasm: TraitScale


class CommunicationStyleProfile(TechnicalSheetBaseModel):
    speech_style: SpeechStyle
    message_length: MessageLength
    emoji_usage: EmojiUsage
    emoji_style: str | None = Field(default=None, min_length=3, max_length=40)
    punctuation_style: PunctuationStyle


class SocialBehaviorProfile(TechnicalSheetBaseModel):
    fan_relationship_style: FanRelationshipStyle
    attention_strategy: AttentionStrategy
    response_energy: ResponseEnergy
    jealousy_play: JealousyPlayLevel


class PersonalityProfile(TechnicalSheetBaseModel):
    archetype: ArchetypeCode
    voice_tone: VoiceTone
    primary_traits: list[str] = Field(min_length=2, max_length=8)
    secondary_traits: list[str] = Field(default_factory=list, max_length=8)
    interaction_style: str = Field(min_length=8, max_length=160)
    axes: PersonalityAxes
    communication_style: CommunicationStyleProfile
    social_behavior: SocialBehaviorProfile


class NarrativeMinimalProfile(TechnicalSheetBaseModel):
    origin: str = Field(min_length=24, max_length=240)
    interests: list[str] = Field(min_length=2, max_length=10)
    daily_life: str = Field(min_length=24, max_length=240)
    motivation: str = Field(min_length=24, max_length=200)
    relationship_with_fans: str = Field(min_length=24, max_length=200)


class NarrativeProfile(TechnicalSheetBaseModel):
    archetype_summary: str = Field(min_length=24, max_length=240)
    origin_story: str = Field(min_length=24, max_length=320)
    motivations: list[str] = Field(min_length=2, max_length=8)
    interests: list[str] = Field(min_length=2, max_length=10)
    audience_role: AudienceRole
    conversational_hooks: list[str] = Field(min_length=2, max_length=8)
    minimal_viable_profile: NarrativeMinimalProfile


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
    conversation_openers: list[str] = Field(default_factory=list, max_length=6)
    emotional_triggers: list[str] = Field(default_factory=list, max_length=8)
    fantasy_pillars: list[str] = Field(default_factory=list, max_length=8)
    relationship_progression: str | None = Field(default=None, min_length=8, max_length=200)
    tone_guardrails: list[str] = Field(default_factory=list, max_length=8)


class FieldTrace(TechnicalSheetBaseModel):
    field_path: str = Field(min_length=3, max_length=120)
    origin: FieldOrigin
    source_text: str | None = Field(default=None, min_length=3, max_length=200)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    rationale: str | None = Field(default=None, min_length=8, max_length=200)


class TraceabilityMetadata(TechnicalSheetBaseModel):
    source_issue_id: str = Field(pattern=r"^[A-Z]+-\d+$")
    source_epic_id: str = Field(pattern=r"^[A-Z]+-\d+$")
    contract_owner: str = Field(min_length=3, max_length=80)
    future_systems_ready: list[Literal["system_2", "system_5"]] = Field(min_length=1, max_length=2)
    last_reviewed_at: datetime
    field_traces: list[FieldTrace] = Field(default_factory=list, max_length=40)


class TechnicalSheet(TechnicalSheetBaseModel):
    schema_version: TechnicalSheetSchemaVersion = TechnicalSheetSchemaVersion.V1
    identity_metadata: IdentityMetadata
    identity_core: IdentityCore
    visual_profile: VisualProfile
    personality_profile: PersonalityProfile
    narrative_profile: NarrativeProfile
    operational_limits: OperationalLimits
    system5_slots: System5Slots
    traceability: TraceabilityMetadata

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_payload(cls, payload: object) -> object:
        if not isinstance(payload, dict):
            return payload

        data = dict(payload)
        identity_core = dict(data.get("identity_core", {}))
        visual_profile = dict(data.get("visual_profile", {}))
        personality_profile = dict(data.get("personality_profile", {}))
        axes = dict(personality_profile.get("axes", {}))
        narrative_profile = dict(data.get("narrative_profile", {}))

        if "identity_metadata" not in data:
            wardrobe_styles = visual_profile.get("wardrobe_styles", [])
            inferred_style = IdentityStyle.PREMIUM if any("luxury" in item for item in wardrobe_styles) else IdentityStyle.EDITORIAL
            data["identity_metadata"] = {
                "avatar_id": None,
                "category": CreationCategory.ADULT_CREATOR,
                "vertical": Vertical.ADULT_ENTERTAINMENT,
                "style": inferred_style,
                "occupation_or_content_basis": "premium digital performer",
            }

        if "archetype" not in personality_profile:
            personality_profile["archetype"] = ArchetypeCode.LUXURY_MUSE
        if "communication_style" not in personality_profile:
            personality_profile["communication_style"] = {
                "speech_style": SpeechStyle.REFINED,
                "message_length": MessageLength.MEDIUM,
                "emoji_usage": EmojiUsage.MODERATE,
                "emoji_style": "sparkles",
                "punctuation_style": PunctuationStyle.POLISHED,
            }
        if "social_behavior" not in personality_profile:
            personality_profile["social_behavior"] = {
                "fan_relationship_style": FanRelationshipStyle.ASPIRATIONAL_MUSE,
                "attention_strategy": AttentionStrategy.BALANCED,
                "response_energy": ResponseEnergy.MEDIUM,
                "jealousy_play": JealousyPlayLevel.LIGHT,
            }
        if {"formality", "warmth", "dominance", "provocation", "accessibility"} & axes.keys():
            personality_profile["axes"] = {
                "dominance": axes.get("dominance", TraitScale.MEDIUM),
                "warmth": axes.get("warmth", TraitScale.HIGH),
                "playfulness": axes.get("accessibility", TraitScale.MEDIUM),
                "mystery": TraitScale.HIGH if axes.get("formality") == "high" else TraitScale.MEDIUM,
                "flirtiness": axes.get("provocation", TraitScale.MEDIUM),
                "intelligence": TraitScale.HIGH if axes.get("formality") in {"medium", "high"} else TraitScale.MEDIUM,
                "sarcasm": TraitScale.MEDIUM,
            }

        if "minimal_viable_profile" not in narrative_profile:
            motivations = narrative_profile.get("motivations", [])
            primary_motivation = motivations[0] if motivations else "protect_brand_consistency"
            narrative_profile["minimal_viable_profile"] = {
                "origin": narrative_profile.get(
                    "origin_story",
                    "Identidad sintetica creada para mantener consistencia visual y narrativa comercial.",
                ),
                "interests": narrative_profile.get("interests", ["fashion", "nightlife"]),
                "daily_life": "Alterna presencia social, contenido curado y rituales esteticos repetibles.",
                "motivation": f"Prioriza {primary_motivation} como objetivo rector de la identidad sintetica.",
                "relationship_with_fans": "Se relaciona con cercania medida y una sensacion de exclusividad sostenida.",
            }

        data["identity_core"] = identity_core
        data["visual_profile"] = visual_profile
        data["personality_profile"] = personality_profile
        data["narrative_profile"] = narrative_profile
        return data


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
