from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from vixenbliss_creator.contracts.common import ContractBaseModel
from vixenbliss_creator.contracts.identity import AllowedContentMode, TechnicalSheet


class CompletionStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class CritiqueIssue(ContractBaseModel):
    code: str = Field(pattern=r"^[a-z0-9_]+$", min_length=3, max_length=64)
    message: str = Field(min_length=8, max_length=280)
    source_node: str = Field(min_length=3, max_length=64)
    retryable: bool = True


class ExpansionResult(ContractBaseModel):
    expansion_summary: str = Field(min_length=24, max_length=320)
    prompt_blueprint: str = Field(min_length=24, max_length=600)
    assumptions: list[str] = Field(default_factory=list, max_length=8)
    technical_sheet_payload: TechnicalSheet


class CopilotRecommendation(ContractBaseModel):
    workflow_id: str = Field(min_length=3, max_length=120)
    base_model_id: str = Field(min_length=3, max_length=120)
    node_ids: list[str] = Field(min_length=1, max_length=24)
    prompt_template: str = Field(min_length=12, max_length=600)
    negative_prompt: str = Field(min_length=12, max_length=400)
    rationale: str = Field(min_length=12, max_length=320)
    content_modes_supported: list[AllowedContentMode] = Field(min_length=1, max_length=3)


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
    attempt_count: int = Field(default=0, ge=0, le=10)
    max_attempts: int = Field(default=2, ge=1, le=10)
    completion_status: CompletionStatus = CompletionStatus.PENDING
    expanded_context: ExpansionResult | None = None
    copilot_recommendation: CopilotRecommendation | None = None
    validation_result: ValidationOutcome | None = None
    critique_history: list[CritiqueIssue] = Field(default_factory=list, max_length=20)
    final_technical_sheet_payload: TechnicalSheet | None = None
    terminal_error_message: str | None = Field(default=None, min_length=8, max_length=280)

    @model_validator(mode="after")
    def validate_consistency(self) -> "GraphState":
        if self.attempt_count > self.max_attempts:
            raise ValueError("attempt_count cannot exceed max_attempts")
        if self.completion_status == CompletionStatus.SUCCEEDED:
            if self.final_technical_sheet_payload is None:
                raise ValueError("succeeded state requires final_technical_sheet_payload")
            if self.validation_result is None or not self.validation_result.valid:
                raise ValueError("succeeded state requires a valid validation_result")
            if self.terminal_error_message is not None:
                raise ValueError("succeeded state cannot define terminal_error_message")
        if self.completion_status == CompletionStatus.FAILED and self.terminal_error_message is None:
            raise ValueError("failed state requires terminal_error_message")
        return self

    def as_graph_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="python")

    @classmethod
    def from_graph_dict(cls, payload: dict[str, Any]) -> "GraphState":
        return cls.model_validate(payload)
