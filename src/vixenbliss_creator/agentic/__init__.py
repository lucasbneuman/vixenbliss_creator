from __future__ import annotations

from .config import AgenticSettings
from .models import (
    CoherenceReport,
    CompletionStatus,
    CopilotRecommendation,
    CopilotStage,
    CreationMode,
    CritiqueIssue,
    ExpansionResult,
    GraphState,
    IdentityCompletionReport,
    IdentityConstraints,
    IdentityDraft,
    OperatorIntent,
    ValidationOutcome,
)

__all__ = [
    "AgenticBrain",
    "AgenticSettings",
    "CoherenceReport",
    "CompletionStatus",
    "CopilotRecommendation",
    "CopilotStage",
    "CreationMode",
    "CritiqueIssue",
    "ExpansionResult",
    "GraphState",
    "IdentityCompletionReport",
    "IdentityConstraints",
    "IdentityDraft",
    "OperatorIntent",
    "TechnicalSheetGraphValidator",
    "ValidationOutcome",
    "build_agentic_brain",
]


def __getattr__(name: str):
    if name in {"AgenticBrain", "build_agentic_brain"}:
        from .graph import AgenticBrain, build_agentic_brain

        return {"AgenticBrain": AgenticBrain, "build_agentic_brain": build_agentic_brain}[name]
    if name == "TechnicalSheetGraphValidator":
        from .validator import TechnicalSheetGraphValidator

        return TechnicalSheetGraphValidator
    raise AttributeError(name)
