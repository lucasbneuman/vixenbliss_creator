from __future__ import annotations

from .models import CritiqueIssue, GraphState, ValidationOutcome


class TechnicalSheetGraphValidator:
    def validate(self, state: GraphState) -> ValidationOutcome:
        issues: list[CritiqueIssue] = []

        if state.expanded_context is None:
            issues.append(
                CritiqueIssue(
                    code="missing_expansion",
                    message="Expansion result is required before validation.",
                    source_node="validator",
                )
            )
            return ValidationOutcome(valid=False, issues=issues, final_payload_consumable=False)

        if state.copilot_recommendation is None:
            issues.append(
                CritiqueIssue(
                    code="missing_copilot_recommendation",
                    message="Copilot recommendation is required before validation.",
                    source_node="validator",
                )
            )
            return ValidationOutcome(valid=False, issues=issues, final_payload_consumable=False)

        payload = state.expanded_context.technical_sheet_payload
        allowed_modes = payload.operational_limits.allowed_content_modes
        supported_modes = state.copilot_recommendation.content_modes_supported

        if not payload.operational_limits.hard_limits:
            issues.append(
                CritiqueIssue(
                    code="missing_hard_limits",
                    message="Operational limits must include at least one hard limit.",
                    source_node="validator",
                )
            )
        if not payload.operational_limits.escalation_triggers:
            issues.append(
                CritiqueIssue(
                    code="missing_escalation_triggers",
                    message="Operational limits must define escalation triggers.",
                    source_node="validator",
                )
            )
        if not set(allowed_modes).issubset(set(supported_modes)):
            issues.append(
                CritiqueIssue(
                    code="copilot_mode_mismatch",
                    message="Copilot recommendation does not support all allowed content modes.",
                    source_node="validator",
                )
            )
        if not state.copilot_recommendation.node_ids:
            issues.append(
                CritiqueIssue(
                    code="empty_copilot_nodes",
                    message="Copilot recommendation must include consumable node identifiers.",
                    source_node="validator",
                )
            )

        try:
            payload_json = payload.model_dump(mode="json")
            payload.__class__.model_validate(payload_json)
        except Exception as exc:  # pragma: no cover
            issues.append(
                CritiqueIssue(
                    code="payload_not_stable",
                    message=f"Technical sheet payload is not stably serializable: {exc}",
                    source_node="validator",
                    retryable=False,
                )
            )

        if issues:
            return ValidationOutcome(valid=False, issues=issues, final_payload_consumable=False)
        return ValidationOutcome(valid=True, issues=[], final_payload_consumable=True)
