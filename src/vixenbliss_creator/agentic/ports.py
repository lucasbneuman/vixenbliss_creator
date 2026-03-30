from __future__ import annotations

from typing import Protocol

from .models import CopilotRecommendation, CritiqueIssue, ExpansionResult, GraphState, ValidationOutcome


class LLMClient(Protocol):
    def generate_expansion(
        self,
        idea: str,
        critique_history: list[CritiqueIssue],
        attempt_count: int,
    ) -> ExpansionResult:
        ...


class CopilotClient(Protocol):
    def recommend_workflow(self, expansion: ExpansionResult) -> CopilotRecommendation:
        ...


class GraphValidator(Protocol):
    def validate(self, state: GraphState) -> ValidationOutcome:
        ...
