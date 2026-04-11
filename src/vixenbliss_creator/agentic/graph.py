from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .adapters import ComfyUICopilotHTTPClient, OpenAICompatibleLLMClient
from .config import AgenticSettings
from .models import (
    CoherenceReport,
    CompletionStatus,
    CopilotStage,
    CreationMode,
    CritiqueDomain,
    CritiqueIssue,
    GraphState,
    IdentityConstraints,
    OperatorIntent,
)
from .ports import CopilotClient, GraphValidator, LLMClient
from .validator import TechnicalSheetGraphValidator
from .workflow_registry import WorkflowRegistry
from vixenbliss_creator.traceability import normalize_trace_source_text
from vixenbliss_creator.contracts.identity import (
    ArchetypeCode,
    CreationCategory,
    FieldTrace,
    FieldOrigin,
    IdentityStyle,
    SpeechStyle,
    Vertical,
    VoiceTone,
)


def _capped_field_list(values: list[str], *, limit: int = 24) -> list[str]:
    return list(dict.fromkeys(values))[:limit]


def _trim_error_message(prefix: str, exc: Exception, limit: int = 280) -> str:
    message = f"{prefix}: {exc}"
    return message if len(message) <= limit else message[: limit - 3] + "..."


class GraphStateDict(TypedDict, total=False):
    input_idea: str
    operator_intent: Any
    creation_mode: str
    explicit_constraints: Any
    normalized_constraints: Any
    manually_defined_fields: list[str]
    inferred_fields: list[str]
    missing_fields: list[str]
    attempt_count: int
    max_attempts: int
    completion_status: str
    identity_draft: Any
    expanded_context: Any
    copilot_recommendation: Any
    coherence_report: Any
    validation_result: Any
    critique_history: list[Any]
    final_technical_sheet_payload: Any
    terminal_error_message: str | None
    copilot_notes: list[str]


class AgenticBrain:
    def __init__(
        self,
        llm_client: LLMClient,
        copilot_client: CopilotClient,
        validator: GraphValidator,
        max_attempts: int = 2,
        workflow_registry: WorkflowRegistry | None = None,
        copilot_default_stage: CopilotStage = CopilotStage.S1_IDENTITY_IMAGE,
    ) -> None:
        self.llm_client = llm_client
        self.copilot_client = copilot_client
        self.validator = validator
        self.max_attempts = max_attempts
        self.workflow_registry = workflow_registry or WorkflowRegistry.default()
        self.copilot_default_stage = copilot_default_stage
        self._graph = self._build_graph()

    def invoke(self, state: GraphState) -> GraphState:
        seed = state.model_copy(update={"max_attempts": self.max_attempts})
        result = self._graph.invoke(
            seed.as_graph_dict(),
            {"recursion_limit": max(25, self.max_attempts * 20)},
        )
        return GraphState.from_graph_dict(result)

    def _build_graph(self):
        graph = StateGraph(GraphStateDict)
        graph.add_node("detect_operator_intent", self._detect_operator_intent_node)
        graph.add_node("detect_creation_mode", self._detect_creation_mode_node)
        graph.add_node("extract_personality_constraints", self._extract_constraints_node)
        graph.add_node("normalize_constraints", self._normalize_constraints_node)
        graph.add_node("complete_identity_profile", self._expansion_node)
        graph.add_node("validate_profile_coherence", self._validate_profile_coherence_node)
        graph.add_node("generate_technical_sheet", self._generate_technical_sheet_node)
        graph.add_node("request_copilot_recommendation", self._copilot_node)
        graph.add_node("validate_final_payload", self._validator_node)
        graph.add_node("critique_and_retry", self._critique_router_node)
        graph.add_node("finalize_graph_state", self._finalize_node)

        graph.add_edge(START, "detect_operator_intent")
        graph.add_edge("detect_operator_intent", "detect_creation_mode")
        graph.add_edge("detect_creation_mode", "extract_personality_constraints")
        graph.add_edge("extract_personality_constraints", "normalize_constraints")
        graph.add_edge("normalize_constraints", "complete_identity_profile")
        graph.add_edge("complete_identity_profile", "validate_profile_coherence")
        graph.add_edge("validate_profile_coherence", "generate_technical_sheet")
        graph.add_edge("generate_technical_sheet", "request_copilot_recommendation")
        graph.add_edge("request_copilot_recommendation", "validate_final_payload")
        graph.add_edge("validate_final_payload", "critique_and_retry")
        graph.add_conditional_edges(
            "critique_and_retry",
            self._route_after_critique,
            {
                "detect_operator_intent": "detect_operator_intent",
                "normalize_constraints": "normalize_constraints",
                "complete_identity_profile": "complete_identity_profile",
                "generate_technical_sheet": "generate_technical_sheet",
                "request_copilot_recommendation": "request_copilot_recommendation",
                "finalize_graph_state": "finalize_graph_state",
            },
        )
        graph.add_edge("finalize_graph_state", END)
        return graph.compile()

    def _detect_operator_intent_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.completion_status == CompletionStatus.FAILED:
            return state.as_graph_dict()

        idea = state.input_idea.lower()
        requested_attributes: list[str] = []
        for token, field_path in (
            ("arquetipo", "archetype"),
            ("dominant queen", "archetype"),
            ("sarc", "personality_axes.sarcasm"),
            ("casual", "communication_style.speech_style"),
            ("premium", "metadata.style"),
            ("lifestyle", "metadata.vertical"),
            ("estilo", "metadata.style"),
            ("categoria", "metadata.category"),
            ("narrativa", "narrative_minimal"),
        ):
            if token in idea and field_path not in requested_attributes:
                requested_attributes.append(field_path)

        automation_hint = "full_auto"
        if "resto automatic" in idea or "automático" in idea or "automatico" in idea:
            automation_hint = "partial_auto"
        elif "solo" in idea or "yo quiero" in idea or "quiero elegir" in idea:
            automation_hint = "guided_manual"

        wants_new_avatar = "avatar" in idea or "personaje" in idea or "nuevo" in idea or "creá" in idea or "crea" in idea
        intent = OperatorIntent(
            action="create_avatar_identity",
            wants_new_avatar=wants_new_avatar,
            requested_attributes=requested_attributes,
            automation_hint=automation_hint,
            specificity_level=min(len(requested_attributes) * 2, 10),
        )
        return state.model_copy(update={"operator_intent": intent}).as_graph_dict()

    def _detect_creation_mode_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.operator_intent is None:
            return state.model_copy(
                update={
                    "completion_status": CompletionStatus.FAILED,
                    "terminal_error_message": "Operator intent is required before selecting creation mode.",
                }
            ).as_graph_dict()

        idea = state.input_idea.lower()
        explicit_count = len(state.operator_intent.requested_attributes)
        if explicit_count == 0:
            mode = CreationMode.AUTOMATIC
        elif "creá un avatar" in idea or "crea un avatar" in idea:
            mode = CreationMode.AUTOMATIC
        elif "resto automatic" in idea or "resto automático" in idea:
            mode = CreationMode.SEMI_AUTOMATIC
        elif "quiero elegir" in idea or explicit_count <= 2:
            mode = CreationMode.HYBRID_BY_ATTRIBUTE
        else:
            mode = CreationMode.MANUAL
        return state.model_copy(update={"creation_mode": mode}).as_graph_dict()

    def _extract_constraints_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.completion_status == CompletionStatus.FAILED:
            return state.as_graph_dict()

        idea = state.input_idea.lower()
        fields: list[str] = []
        constraints = IdentityConstraints(source_excerpt=state.input_idea)

        if "lifestyle premium" in idea or "lifestyle" in idea:
            constraints.vertical = Vertical.LIFESTYLE
            fields.append("metadata.vertical")
        if "premium" in idea:
            constraints.style = IdentityStyle.PREMIUM
            fields.append("metadata.style")
        if "casual" in idea:
            constraints.speech_style = SpeechStyle.CASUAL
            fields.append("communication_style.speech_style")
        if "sarc" in idea:
            fields.append("personality_axes.sarcasm")
        if "dominant queen" in idea or "dominant_queen" in idea:
            constraints.archetype = ArchetypeCode.DOMINANT_QUEEN
            fields.append("archetype")
        if "glam" in idea:
            constraints.style = IdentityStyle.GLAM
            if "metadata.style" not in fields:
                fields.append("metadata.style")
        if "categoría" in idea or "categoria" in idea:
            fields.append("metadata.category")
        if "estilo" in idea:
            fields.append("metadata.style")
        if "narrativa" in idea:
            fields.append("narrative_minimal")

        constraints.explicitly_defined_fields = fields
        return state.model_copy(
            update={
                "explicit_constraints": constraints,
                "manually_defined_fields": fields,
            }
        ).as_graph_dict()

    def _normalize_constraints_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.explicit_constraints is None:
            return state.model_copy(
                update={
                    "completion_status": CompletionStatus.FAILED,
                    "terminal_error_message": "Explicit constraints are required before normalization.",
                }
            ).as_graph_dict()

        normalized = state.explicit_constraints.model_copy(deep=True)
        if normalized.vertical is None:
            normalized.vertical = Vertical.ADULT_ENTERTAINMENT
        if normalized.category is None:
            normalized.category = (
                CreationCategory.LIFESTYLE_PREMIUM
                if normalized.vertical == Vertical.LIFESTYLE
                else CreationCategory.ADULT_CREATOR
            )
        if normalized.style is None:
            normalized.style = IdentityStyle.PREMIUM if normalized.vertical == Vertical.LIFESTYLE else IdentityStyle.EDITORIAL
        if normalized.occupation_or_content_basis is None:
            normalized.occupation_or_content_basis = (
                "luxury lifestyle creator"
                if normalized.vertical == Vertical.LIFESTYLE
                else "premium digital performer"
            )
        if normalized.archetype is None:
            normalized.archetype = (
                ArchetypeCode.LUXURY_MUSE
                if normalized.vertical == Vertical.LIFESTYLE
                else ArchetypeCode.PLAYFUL_TEASE
            )
        if normalized.speech_style is None:
            normalized.speech_style = SpeechStyle.REFINED if normalized.style == IdentityStyle.PREMIUM else SpeechStyle.CASUAL
        if normalized.voice_tone is None:
            normalized.voice_tone = VoiceTone.SEDUCTIVE if normalized.vertical != Vertical.LIFESTYLE else VoiceTone.AUTHORITATIVE

        inferred = [
            field_path
            for field_path, value in (
                ("metadata.vertical", normalized.vertical),
                ("metadata.category", normalized.category),
                ("metadata.style", normalized.style),
                ("metadata.occupation_or_content_basis", normalized.occupation_or_content_basis),
                ("archetype", normalized.archetype),
                ("communication_style.speech_style", normalized.speech_style),
                ("voice_tone", normalized.voice_tone),
            )
            if value is not None and field_path not in state.manually_defined_fields
        ]
        return state.model_copy(
            update={
                "normalized_constraints": normalized,
                "inferred_fields": inferred,
            }
        ).as_graph_dict()

    def _expansion_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.completion_status == CompletionStatus.FAILED:
            return state.as_graph_dict()
        if state.normalized_constraints is None:
            return state.model_copy(
                update={
                    "completion_status": CompletionStatus.FAILED,
                    "terminal_error_message": "Normalized constraints are required before identity completion.",
                }
            ).as_graph_dict()

        attempt_count = state.attempt_count + 1
        try:
            expanded = self.llm_client.generate_expansion(
                idea=state.input_idea,
                critique_history=state.critique_history,
                attempt_count=attempt_count,
            )
        except Exception as exc:
            return state.model_copy(
                update={
                    "attempt_count": attempt_count,
                    "completion_status": CompletionStatus.FAILED,
                    "terminal_error_message": _trim_error_message("Expansion failed explicitly", exc),
                }
            ).as_graph_dict()

        completion = expanded.completion_report
        trace_map = expanded.identity_draft.trace_map()
        merged_manual_fields = _capped_field_list([
            field_path
            for field_path in list(dict.fromkeys([*state.manually_defined_fields, *completion.manually_defined_fields]))
            if field_path != "field.path"
        ])
        merged_inferred_fields = _capped_field_list([
            field_path
            for field_path in list(dict.fromkeys([*state.inferred_fields, *completion.inferred_fields]))
            if field_path not in merged_manual_fields and field_path != "field.path"
        ])
        merged_traces = list(expanded.identity_draft.field_traces)
        for field_path in merged_manual_fields:
            if field_path not in trace_map:
                merged_traces.append(
                    FieldTrace(
                        field_path=field_path,
                        origin=FieldOrigin.MANUAL,
                        source_text=normalize_trace_source_text(state.input_idea),
                        confidence=1.0,
                        rationale="Campo manual preservado desde la extraccion inicial de constraints.",
                    )
                )
        trace_map = {trace.field_path: trace for trace in merged_traces}
        for field_path in merged_inferred_fields:
            if field_path not in trace_map:
                merged_traces.append(
                    FieldTrace(
                        field_path=field_path,
                        origin=FieldOrigin.INFERRED,
                        source_text=normalize_trace_source_text(state.input_idea),
                        confidence=0.8,
                        rationale="Campo inferido preservado para mantener trazabilidad del draft final.",
                    )
                )
        patched_identity_draft = expanded.identity_draft.model_copy(update={"field_traces": merged_traces})
        patched_expanded = expanded.model_copy(
            update={
                "identity_draft": patched_identity_draft,
                "completion_report": completion.model_copy(
                    update={
                        "manually_defined_fields": merged_manual_fields,
                        "inferred_fields": merged_inferred_fields,
                    }
                ),
            }
        )
        return state.model_copy(
            update={
                "attempt_count": attempt_count,
                "expanded_context": patched_expanded,
                "normalized_constraints": patched_expanded.normalized_constraints,
                "identity_draft": patched_identity_draft,
                "manually_defined_fields": merged_manual_fields,
                "inferred_fields": merged_inferred_fields,
                "missing_fields": _capped_field_list(completion.missing_fields),
                "coherence_report": None,
                "copilot_recommendation": None,
                "validation_result": None,
                "final_technical_sheet_payload": None,
                "terminal_error_message": None,
            }
        ).as_graph_dict()

    def _validate_profile_coherence_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.completion_status == CompletionStatus.FAILED:
            return state.as_graph_dict()
        if state.identity_draft is None:
            return state.model_copy(
                update={
                    "completion_status": CompletionStatus.FAILED,
                    "terminal_error_message": "Identity draft is required before coherence validation.",
                }
            ).as_graph_dict()

        issues: list[CritiqueIssue] = []
        draft = state.identity_draft
        metadata = draft.metadata
        axes = draft.personality_axes
        communication = draft.communication_style
        social = draft.social_behavior

        if state.missing_fields:
            issues.append(
                CritiqueIssue(
                    code="identity_fields_missing",
                    message="Identity draft still contains missing fields after completion.",
                    source_node="validate_profile_coherence",
                    domain=CritiqueDomain.IDENTITY,
                    target_node="complete_identity_profile",
                )
            )
        if metadata.vertical == Vertical.LIFESTYLE and draft.archetype == ArchetypeCode.DOMINANT_QUEEN:
            issues.append(
                CritiqueIssue(
                    code="vertical_archetype_conflict",
                    message="Lifestyle vertical should not default to dominant queen without stronger operator intent.",
                    source_node="validate_profile_coherence",
                    domain=CritiqueDomain.OPERATIONAL_LIMITS,
                    target_node="normalize_constraints",
                )
            )
        if metadata.vertical == Vertical.LIFESTYLE and axes.sarcasm == "very_high":
            issues.append(
                CritiqueIssue(
                    code="lifestyle_sarcasm_conflict",
                    message="Lifestyle vertical cannot sustain extremely high sarcasm as a default commercial tone.",
                    source_node="validate_profile_coherence",
                    domain=CritiqueDomain.IDENTITY,
                    target_node="complete_identity_profile",
                )
            )
        if axes.warmth in {"very_low", "low"} and social.fan_relationship_style == "close_confidant":
            issues.append(
                CritiqueIssue(
                    code="fan_relationship_conflict",
                    message="Cold personalities cannot present a close-confidant fan relationship without contradiction.",
                    source_node="validate_profile_coherence",
                    domain=CritiqueDomain.IDENTITY,
                    target_node="complete_identity_profile",
                )
            )
        if communication.speech_style == SpeechStyle.CASUAL and metadata.style == IdentityStyle.PREMIUM and axes.sarcasm == "very_high":
            issues.append(
                CritiqueIssue(
                    code="premium_tone_conflict",
                    message="Premium style with casual speech and extreme sarcasm requires a more coherent blend.",
                    source_node="validate_profile_coherence",
                    domain=CritiqueDomain.IDENTITY,
                    target_node="complete_identity_profile",
                )
            )

        report = CoherenceReport(valid=not issues, issues=issues)
        return state.model_copy(update={"coherence_report": report}).as_graph_dict()

    def _generate_technical_sheet_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.completion_status == CompletionStatus.FAILED:
            return state.as_graph_dict()
        if state.expanded_context is None:
            return state.model_copy(
                update={
                    "completion_status": CompletionStatus.FAILED,
                    "terminal_error_message": "Expanded context is required before generating the technical sheet.",
                }
            ).as_graph_dict()
        return state.as_graph_dict()

    def _copilot_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.expanded_context is None or state.completion_status == CompletionStatus.FAILED:
            return state.as_graph_dict()

        try:
            recommendation = self.copilot_client.recommend_workflow(state.expanded_context)
        except Exception as exc:
            note = _trim_error_message("Copilot degraded to approved fallback", exc)
            return state.model_copy(
                update={
                    "copilot_recommendation": self.workflow_registry.build_fallback_recommendation(self.copilot_default_stage),
                    "copilot_notes": [*state.copilot_notes, note][-8:],
                }
            ).as_graph_dict()
        return state.model_copy(update={"copilot_recommendation": recommendation}).as_graph_dict()

    def _validator_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.completion_status == CompletionStatus.FAILED:
            return state.as_graph_dict()
        try:
            outcome = self.validator.validate(state)
        except Exception as exc:
            return state.model_copy(
                update={
                    "completion_status": CompletionStatus.FAILED,
                    "terminal_error_message": _trim_error_message("Validation failed explicitly", exc),
                }
            ).as_graph_dict()
        return state.model_copy(update={"validation_result": outcome}).as_graph_dict()

    def _critique_router_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.completion_status == CompletionStatus.FAILED:
            return state.as_graph_dict()

        pending_issues: list[CritiqueIssue] = []
        if state.coherence_report is not None and not state.coherence_report.valid:
            pending_issues.extend(state.coherence_report.issues)
        if state.validation_result is not None and not state.validation_result.valid:
            pending_issues.extend(state.validation_result.issues)

        if not pending_issues:
            return state.as_graph_dict()

        critique_history = [*state.critique_history, *pending_issues][-20:]
        terminal = state.attempt_count >= state.max_attempts or any(issue.retryable is False for issue in pending_issues)
        if terminal:
            issue_messages = "; ".join(issue.message for issue in pending_issues)
            return state.model_copy(
                update={
                    "critique_history": critique_history,
                    "completion_status": CompletionStatus.FAILED,
                    "terminal_error_message": f"Graph validation exhausted retries: {issue_messages}",
                }
            ).as_graph_dict()
        return state.model_copy(update={"critique_history": critique_history}).as_graph_dict()

    def _route_after_critique(self, raw_state: GraphStateDict) -> str:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.completion_status == CompletionStatus.FAILED:
            return "finalize_graph_state"
        if state.validation_result is not None and state.validation_result.valid:
            return "finalize_graph_state"
        if state.coherence_report is not None and not state.coherence_report.valid:
            return self._select_retry_target(state.coherence_report.issues)
        if state.validation_result is not None and not state.validation_result.valid:
            return self._select_retry_target(state.validation_result.issues)
        return "complete_identity_profile"

    def _select_retry_target(self, issues: list[CritiqueIssue]) -> str:
        for issue in issues:
            if issue.target_node in {
                "detect_operator_intent",
                "normalize_constraints",
                "complete_identity_profile",
                "generate_technical_sheet",
                "request_copilot_recommendation",
            }:
                return issue.target_node
        return "complete_identity_profile"

    def _finalize_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if (
            state.validation_result is not None
            and state.validation_result.valid
            and state.expanded_context is not None
            and state.identity_draft is not None
            and not state.missing_fields
        ):
            return state.model_copy(
                update={
                    "completion_status": CompletionStatus.SUCCEEDED,
                    "final_technical_sheet_payload": state.expanded_context.technical_sheet_payload,
                }
            ).as_graph_dict()
        if state.completion_status == CompletionStatus.PENDING:
            return state.model_copy(
                update={
                    "completion_status": CompletionStatus.FAILED,
                    "terminal_error_message": "Graph terminated without a final valid GraphState.",
                }
            ).as_graph_dict()
        return state.as_graph_dict()


def build_agentic_brain(
    settings: AgenticSettings | None = None,
    llm_client: LLMClient | None = None,
    copilot_client: CopilotClient | None = None,
    validator: GraphValidator | None = None,
) -> AgenticBrain:
    settings = settings or AgenticSettings.from_env()
    llm_client = llm_client or OpenAICompatibleLLMClient(settings)
    copilot_client = copilot_client or ComfyUICopilotHTTPClient(settings)
    workflow_registry = WorkflowRegistry.default()
    validator = validator or TechnicalSheetGraphValidator(workflow_registry=workflow_registry)
    return AgenticBrain(
        llm_client=llm_client,
        copilot_client=copilot_client,
        validator=validator,
        max_attempts=settings.max_attempts,
        workflow_registry=workflow_registry,
        copilot_default_stage=settings.comfyui_copilot_default_stage,
    )
