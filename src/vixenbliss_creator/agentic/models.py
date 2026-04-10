from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from vixenbliss_creator.contracts.common import ContractBaseModel
from vixenbliss_creator.contracts.identity import (
    ArchetypeCode,
    CreationCategory,
    FieldOrigin,
    FieldTrace,
    IdentityMetadata,
    IdentityStyle,
    NarrativeMinimalProfile,
    PersonalityAxes,
    SocialBehaviorProfile,
    SpeechStyle,
    TechnicalSheet,
    Vertical,
    VoiceTone,
    CommunicationStyleProfile,
)


class CompletionStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class CreationMode(str, Enum):
    MANUAL = "manual"
    SEMI_AUTOMATIC = "semi_automatic"
    AUTOMATIC = "automatic"
    HYBRID_BY_ATTRIBUTE = "hybrid_by_attribute"


class CritiqueDomain(str, Enum):
    INTENT = "intent"
    CONSTRAINTS = "constraints"
    IDENTITY = "identity"
    TECHNICAL_SHEET = "technical_sheet"
    COPILOT = "copilot"
    OPERATIONAL_LIMITS = "operational_limits"


class CopilotStage(str, Enum):
    S1_IDENTITY_IMAGE = "s1_identity_image"
    S2_CONTENT_IMAGE = "s2_content_image"
    S2_VIDEO = "s2_video"


class OperatorIntent(ContractBaseModel):
    action: str = Field(min_length=3, max_length=80)
    wants_new_avatar: bool = True
    requested_attributes: list[str] = Field(default_factory=list, max_length=16)
    automation_hint: str = Field(default="unspecified", min_length=3, max_length=40)
    specificity_level: int = Field(default=0, ge=0, le=10)


class IdentityConstraints(ContractBaseModel):
    avatar_id: str | None = Field(default=None, min_length=3, max_length=80)
    name: str | None = Field(default=None, min_length=2, max_length=80)
    category: CreationCategory | None = None
    vertical: Vertical | None = None
    style: IdentityStyle | None = None
    occupation_or_content_basis: str | None = Field(default=None, min_length=3, max_length=80)
    archetype: ArchetypeCode | None = None
    speech_style: SpeechStyle | None = None
    voice_tone: VoiceTone | None = None
    explicitly_defined_fields: list[str] = Field(default_factory=list, max_length=24)
    source_excerpt: str | None = Field(default=None, min_length=3, max_length=240)


class IdentityDraft(ContractBaseModel):
    metadata: IdentityMetadata
    name: str = Field(min_length=2, max_length=80)
    archetype: ArchetypeCode
    personality_axes: PersonalityAxes
    communication_style: CommunicationStyleProfile
    social_behavior: SocialBehaviorProfile
    narrative_minimal: NarrativeMinimalProfile
    field_traces: list[FieldTrace] = Field(min_length=1, max_length=40)

    def trace_map(self) -> dict[str, FieldTrace]:
        return {trace.field_path: trace for trace in self.field_traces}


class IdentityCompletionReport(ContractBaseModel):
    manually_defined_fields: list[str] = Field(default_factory=list, max_length=24)
    inferred_fields: list[str] = Field(default_factory=list, max_length=24)
    missing_fields: list[str] = Field(default_factory=list, max_length=24)


class CoherenceReport(ContractBaseModel):
    valid: bool
    issues: list["CritiqueIssue"] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def validate_consistency(self) -> "CoherenceReport":
        if self.valid and self.issues:
            raise ValueError("valid coherence reports must not include issues")
        if not self.valid and not self.issues:
            raise ValueError("invalid coherence reports must include issues")
        return self


class CritiqueIssue(ContractBaseModel):
    code: str = Field(pattern=r"^[a-z0-9_]+$", min_length=3, max_length=64)
    message: str = Field(min_length=8, max_length=280)
    source_node: str = Field(min_length=3, max_length=64)
    domain: CritiqueDomain = CritiqueDomain.IDENTITY
    target_node: str | None = Field(default=None, min_length=3, max_length=64)
    retryable: bool = True


class ExpansionResult(ContractBaseModel):
    expansion_summary: str = Field(min_length=24, max_length=320)
    prompt_blueprint: str = Field(min_length=24, max_length=600)
    assumptions: list[str] = Field(default_factory=list, max_length=8)
    normalized_constraints: IdentityConstraints
    identity_draft: IdentityDraft
    completion_report: IdentityCompletionReport
    technical_sheet_payload: TechnicalSheet


class CopilotRecommendation(ContractBaseModel):
    stage: CopilotStage
    workflow_id: str = Field(min_length=3, max_length=120)
    workflow_version: str = Field(min_length=2, max_length=40)
    recommended_workflow_family: str = Field(min_length=3, max_length=80)
    base_model_id: str = Field(min_length=3, max_length=120)
    required_nodes: list[str] = Field(min_length=1, max_length=24)
    optional_nodes: list[str] = Field(default_factory=list, max_length=24)
    model_hints: list[str] = Field(default_factory=list, max_length=12)
    prompt_template: str = Field(min_length=12, max_length=600)
    negative_prompt: str = Field(min_length=12, max_length=400)
    reasoning_summary: str = Field(min_length=12, max_length=320)
    risk_flags: list[str] = Field(default_factory=list, max_length=12)
    compatibility_notes: list[str] = Field(default_factory=list, max_length=12)
    content_modes_supported: list[str] = Field(min_length=1, max_length=3)
    registry_source: str = Field(default="approved_internal", min_length=3, max_length=80)


class ValidationOutcome(ContractBaseModel):
    valid: bool
    issues: list[CritiqueIssue] = Field(default_factory=list, max_length=12)
    final_payload_consumable: bool = False

    @model_validator(mode="after")
    def validate_consistency(self) -> "ValidationOutcome":
        if self.valid and self.issues:
            raise ValueError("valid outcomes must not include issues")
        if not self.valid and not self.issues:
            raise ValueError("invalid outcomes must include issues")
        if self.valid and not self.final_payload_consumable:
            raise ValueError("valid outcomes must be consumable")
        return self


class GraphState(ContractBaseModel):
    input_idea: str = Field(min_length=8, max_length=600)
    operator_intent: OperatorIntent | None = None
    creation_mode: CreationMode | None = None
    explicit_constraints: IdentityConstraints | None = None
    normalized_constraints: IdentityConstraints | None = None
    manually_defined_fields: list[str] = Field(default_factory=list, max_length=24)
    inferred_fields: list[str] = Field(default_factory=list, max_length=24)
    missing_fields: list[str] = Field(default_factory=list, max_length=24)
    attempt_count: int = Field(default=0, ge=0, le=10)
    max_attempts: int = Field(default=2, ge=1, le=10)
    completion_status: CompletionStatus = CompletionStatus.PENDING
    identity_draft: IdentityDraft | None = None
    expanded_context: ExpansionResult | None = None
    copilot_recommendation: CopilotRecommendation | None = None
    copilot_notes: list[str] = Field(default_factory=list, max_length=8)
    coherence_report: CoherenceReport | None = None
    validation_result: ValidationOutcome | None = None
    critique_history: list[CritiqueIssue] = Field(default_factory=list, max_length=20)
    final_technical_sheet_payload: TechnicalSheet | None = None
    terminal_error_message: str | None = Field(default=None, min_length=8, max_length=280)

    @model_validator(mode="after")
    def validate_consistency(self) -> "GraphState":
        if self.attempt_count > self.max_attempts:
            raise ValueError("attempt_count cannot exceed max_attempts")
        if self.completion_status == CompletionStatus.SUCCEEDED:
            if self.identity_draft is None:
                raise ValueError("succeeded state requires identity_draft")
            if self.final_technical_sheet_payload is None:
                raise ValueError("succeeded state requires final_technical_sheet_payload")
            if self.validation_result is None or not self.validation_result.valid:
                raise ValueError("succeeded state requires a valid validation_result")
            if self.missing_fields:
                raise ValueError("succeeded state cannot define missing_fields")
            if self.terminal_error_message is not None:
                raise ValueError("succeeded state cannot define terminal_error_message")
            self._validate_traceability()
        if self.completion_status == CompletionStatus.FAILED and self.terminal_error_message is None:
            raise ValueError("failed state requires terminal_error_message")
        return self

    def _validate_traceability(self) -> None:
        if self.identity_draft is None:
            return
        trace_map = self.identity_draft.trace_map()
        for field_path in self.manually_defined_fields:
            trace = trace_map.get(field_path)
            if trace is None or trace.origin != FieldOrigin.MANUAL:
                raise ValueError(f"manual field {field_path} must keep manual traceability")
        for field_path in self.inferred_fields:
            trace = trace_map.get(field_path)
            if trace is None or trace.origin not in {FieldOrigin.INFERRED, FieldOrigin.DEFAULTED, FieldOrigin.DERIVED}:
                raise ValueError(f"inferred field {field_path} must keep inferred traceability")
        if self.creation_mode == CreationMode.MANUAL and any(
            trace.origin != FieldOrigin.MANUAL for trace in trace_map.values() if trace.field_path in self.manually_defined_fields
        ):
            raise ValueError("manual creation mode cannot mutate manually defined fields")

    def as_graph_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="python")

    @classmethod
    def from_graph_dict(cls, payload: dict[str, Any]) -> "GraphState":
        return cls.model_validate(payload)
