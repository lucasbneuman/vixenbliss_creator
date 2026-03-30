from __future__ import annotations

from typing import Protocol

from .models import ResumeCheckpoint, StepExecutionResult, VisualGenerationRequest


class VisualExecutionClient(Protocol):
    def render_base_image(self, request: VisualGenerationRequest) -> StepExecutionResult:
        ...

    def run_face_detail(
        self,
        request: VisualGenerationRequest,
        checkpoint: ResumeCheckpoint,
    ) -> StepExecutionResult:
        ...
