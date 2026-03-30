from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .adapters import ComfyUICopilotHTTPClient, OpenAICompatibleLLMClient
from .config import AgenticSettings
from .models import CompletionStatus, GraphState
from .ports import CopilotClient, GraphValidator, LLMClient
from .validator import TechnicalSheetGraphValidator


class GraphStateDict(TypedDict, total=False):
    input_idea: str
    attempt_count: int
    max_attempts: int
    completion_status: str
    expanded_context: Any
    copilot_recommendation: Any
    validation_result: Any
    critique_history: list[Any]
    final_technical_sheet_payload: Any
    terminal_error_message: str | None


class AgenticBrain:
    def __init__(
        self,
        llm_client: LLMClient,
        copilot_client: CopilotClient,
        validator: GraphValidator,
        max_attempts: int = 2,
    ) -> None:
        self.llm_client = llm_client
        self.copilot_client = copilot_client
        self.validator = validator
        self.max_attempts = max_attempts
        self._graph = self._build_graph()

    def invoke(self, state: GraphState) -> GraphState:
        seed = state.model_copy(update={"max_attempts": self.max_attempts})
        result = self._graph.invoke(seed.as_graph_dict())
        return GraphState.from_graph_dict(result)

    def _build_graph(self):
        graph = StateGraph(GraphStateDict)
        graph.add_node("expansion", self._expansion_node)
        graph.add_node("copilot_consultor", self._copilot_node)
        graph.add_node("validator", self._validator_node)
        graph.add_node("critique_router", self._critique_router_node)
        graph.add_node("finalize", self._finalize_node)

        graph.add_edge(START, "expansion")
        graph.add_edge("expansion", "copilot_consultor")
        graph.add_edge("copilot_consultor", "validator")
        graph.add_edge("validator", "critique_router")
        graph.add_conditional_edges(
            "critique_router",
            self._route_after_critique,
            {"expansion": "expansion", "finalize": "finalize"},
        )
        graph.add_edge("finalize", END)
        return graph.compile()

    def _expansion_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.completion_status == CompletionStatus.FAILED:
            return state.as_graph_dict()

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
                    "terminal_error_message": f"Expansion failed explicitly: {exc}",
                }
            ).as_graph_dict()

        return state.model_copy(
            update={
                "attempt_count": attempt_count,
                "expanded_context": expanded,
                "copilot_recommendation": None,
                "validation_result": None,
                "final_technical_sheet_payload": None,
                "terminal_error_message": None,
            }
        ).as_graph_dict()

    def _copilot_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.expanded_context is None or state.completion_status == CompletionStatus.FAILED:
            return state.as_graph_dict()

        try:
            recommendation = self.copilot_client.recommend_workflow(state.expanded_context)
        except Exception as exc:
            return state.model_copy(
                update={
                    "completion_status": CompletionStatus.FAILED,
                    "terminal_error_message": f"Copilot recommendation failed explicitly: {exc}",
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
                    "terminal_error_message": f"Validation failed explicitly: {exc}",
                }
            ).as_graph_dict()
        return state.model_copy(update={"validation_result": outcome}).as_graph_dict()

    def _critique_router_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.completion_status == CompletionStatus.FAILED:
            return state.as_graph_dict()
        if state.validation_result is None:
            return state.model_copy(
                update={
                    "completion_status": CompletionStatus.FAILED,
                    "terminal_error_message": "Validation result is missing before critique routing.",
                }
            ).as_graph_dict()
        if state.validation_result.valid:
            return state.as_graph_dict()

        # Keep the most recent critique issues without breaking GraphState limits.
        critique_history = [*state.critique_history, *state.validation_result.issues][-20:]
        terminal = state.attempt_count >= state.max_attempts or any(
            issue.retryable is False for issue in state.validation_result.issues
        )
        if terminal:
            issue_messages = "; ".join(issue.message for issue in state.validation_result.issues)
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
            return "finalize"
        if state.validation_result is not None and state.validation_result.valid:
            return "finalize"
        return "expansion"

    def _finalize_node(self, raw_state: GraphStateDict) -> GraphStateDict:
        state = GraphState.from_graph_dict(dict(raw_state))
        if state.validation_result is not None and state.validation_result.valid and state.expanded_context is not None:
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
    validator = validator or TechnicalSheetGraphValidator()
    return AgenticBrain(
        llm_client=llm_client,
        copilot_client=copilot_client,
        validator=validator,
        max_attempts=settings.max_attempts,
    )
