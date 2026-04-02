from __future__ import annotations

from .models import CritiqueDomain, CritiqueIssue, GraphState, ValidationOutcome
from vixenbliss_creator.contracts.identity import ArchetypeCode, IdentityStyle, Vertical


class TechnicalSheetGraphValidator:
    def validate(self, state: GraphState) -> ValidationOutcome:
        issues: list[CritiqueIssue] = []

        if state.expanded_context is None:
            issues.append(
                CritiqueIssue(
                    code="missing_expansion",
                    message="Expansion result is required before validation.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.TECHNICAL_SHEET,
                    target_node="complete_identity_profile",
                )
            )
            return ValidationOutcome(valid=False, issues=issues, final_payload_consumable=False)

        if state.identity_draft is None:
            issues.append(
                CritiqueIssue(
                    code="missing_identity_draft",
                    message="Identity draft is required before validation.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.IDENTITY,
                    target_node="complete_identity_profile",
                )
            )
            return ValidationOutcome(valid=False, issues=issues, final_payload_consumable=False)

        if state.copilot_recommendation is None:
            issues.append(
                CritiqueIssue(
                    code="missing_copilot_recommendation",
                    message="Copilot recommendation is required before validation.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.COPILOT,
                    target_node="request_copilot_recommendation",
                )
            )
            return ValidationOutcome(valid=False, issues=issues, final_payload_consumable=False)

        payload = state.expanded_context.technical_sheet_payload
        draft = state.identity_draft
        metadata = draft.metadata
        allowed_modes = payload.operational_limits.allowed_content_modes
        supported_modes = state.copilot_recommendation.content_modes_supported

        if state.missing_fields:
            issues.append(
                CritiqueIssue(
                    code="graph_state_incomplete",
                    message="GraphState cannot finalize while required identity fields are still missing.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.IDENTITY,
                    target_node="complete_identity_profile",
                )
            )
        if not payload.operational_limits.hard_limits:
            issues.append(
                CritiqueIssue(
                    code="missing_hard_limits",
                    message="Operational limits must include at least one hard limit.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.OPERATIONAL_LIMITS,
                    target_node="complete_identity_profile",
                )
            )
        if not payload.operational_limits.escalation_triggers:
            issues.append(
                CritiqueIssue(
                    code="missing_escalation_triggers",
                    message="Operational limits must define escalation triggers.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.OPERATIONAL_LIMITS,
                    target_node="complete_identity_profile",
                )
            )
        if not set(allowed_modes).issubset(set(supported_modes)):
            issues.append(
                CritiqueIssue(
                    code="copilot_mode_mismatch",
                    message="Copilot recommendation does not support all allowed content modes.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.COPILOT,
                    target_node="request_copilot_recommendation",
                )
            )
        if not state.copilot_recommendation.node_ids:
            issues.append(
                CritiqueIssue(
                    code="empty_copilot_nodes",
                    message="Copilot recommendation must include consumable node identifiers.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.COPILOT,
                    target_node="request_copilot_recommendation",
                )
            )

        if payload.identity_metadata.vertical != metadata.vertical:
            issues.append(
                CritiqueIssue(
                    code="vertical_identity_mismatch",
                    message="Technical sheet metadata must preserve the vertical selected for the identity draft.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.TECHNICAL_SHEET,
                    target_node="generate_technical_sheet",
                    retryable=False,
                )
            )
        if payload.identity_metadata.style != metadata.style:
            issues.append(
                CritiqueIssue(
                    code="style_identity_mismatch",
                    message="Technical sheet metadata must preserve the style selected for the identity draft.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.TECHNICAL_SHEET,
                    target_node="complete_identity_profile",
                )
            )
        if payload.personality_profile.archetype != draft.archetype:
            issues.append(
                CritiqueIssue(
                    code="archetype_identity_mismatch",
                    message="Technical sheet personality archetype must match the identity draft.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.TECHNICAL_SHEET,
                    target_node="complete_identity_profile",
                )
            )
        if payload.narrative_profile.minimal_viable_profile.relationship_with_fans != draft.narrative_minimal.relationship_with_fans:
            issues.append(
                CritiqueIssue(
                    code="narrative_fan_relationship_mismatch",
                    message="Technical sheet narrative must remain aligned with the identity draft fan relationship.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.TECHNICAL_SHEET,
                    target_node="complete_identity_profile",
                )
            )

        if metadata.vertical == Vertical.LIFESTYLE and draft.archetype == ArchetypeCode.DOMINANT_QUEEN:
            issues.append(
                CritiqueIssue(
                    code="vertical_business_violation",
                    message="Lifestyle vertical is incompatible with a dominant queen default profile for this task scope.",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.OPERATIONAL_LIMITS,
                    target_node="normalize_constraints",
                    retryable=False,
                )
            )
        if metadata.vertical == Vertical.LIFESTYLE and metadata.style == IdentityStyle.PREMIUM:
            if draft.personality_axes.sarcasm == "very_high":
                issues.append(
                    CritiqueIssue(
                        code="premium_personality_conflict",
                        message="Premium lifestyle identities cannot end with very high sarcasm by default.",
                        source_node="validate_final_payload",
                        domain=CritiqueDomain.IDENTITY,
                        target_node="complete_identity_profile",
                    )
                )
            if draft.communication_style.speech_style == "casual" and draft.social_behavior.fan_relationship_style == "commanding_presence":
                issues.append(
                    CritiqueIssue(
                        code="style_behavior_conflict",
                        message="Casual premium communication cannot combine with a commanding fan relationship in the final profile.",
                        source_node="validate_final_payload",
                        domain=CritiqueDomain.IDENTITY,
                        target_node="complete_identity_profile",
                    )
                )

        trace_map = draft.trace_map()
        for field_path in state.manually_defined_fields:
            trace = trace_map.get(field_path)
            if trace is None or trace.origin != "manual":
                issues.append(
                    CritiqueIssue(
                        code="manual_traceability_lost",
                        message="A manually defined field lost its manual traceability in the final draft.",
                        source_node="validate_final_payload",
                        domain=CritiqueDomain.IDENTITY,
                        target_node="complete_identity_profile",
                        retryable=False,
                    )
                )
                break

        try:
            payload_json = payload.model_dump(mode="json")
            payload.__class__.model_validate(payload_json)
        except Exception as exc:  # pragma: no cover
            issues.append(
                CritiqueIssue(
                    code="payload_not_stable",
                    message=f"Technical sheet payload is not stably serializable: {exc}",
                    source_node="validate_final_payload",
                    domain=CritiqueDomain.TECHNICAL_SHEET,
                    target_node="complete_identity_profile",
                    retryable=False,
                )
            )

        if issues:
            return ValidationOutcome(valid=False, issues=issues, final_payload_consumable=False)
        return ValidationOutcome(valid=True, issues=[], final_payload_consumable=True)
