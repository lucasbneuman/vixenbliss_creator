from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from vixenbliss_creator.agentic.adapters import (
    ComfyUICopilotHTTPClient,
    OpenAICompatibleLLMClient,
)
from vixenbliss_creator.agentic.config import AgenticSettings
from vixenbliss_creator.agentic.graph import build_agentic_brain
from vixenbliss_creator.agentic.models import CompletionStatus, CritiqueIssue, ExpansionResult, GraphState, ValidationOutcome
from vixenbliss_creator.agentic.runner import run_agentic_brain
from vixenbliss_creator.agentic.validator import TechnicalSheetGraphValidator
from vixenbliss_creator.contracts.identity import TechnicalSheet


def build_technical_sheet(*, with_hard_limits: bool = True) -> TechnicalSheet:
    timestamp = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc).isoformat()
    hard_limits = (
        [
            {
                "code": "no_minors",
                "label": "No underage framing",
                "severity": "hard",
                "rationale": "El personaje siempre se representa como adulto ficticio.",
            }
        ]
        if with_hard_limits
        else []
    )
    return TechnicalSheet.model_validate(
        {
            "schema_version": "1.0.0",
            "identity_core": {
                "display_name": "Velvet Ember",
                "fictional_age_years": 25,
                "locale": "es-AR",
                "primary_language": "spanish",
                "secondary_languages": ["english"],
                "tagline": "Performer premium con consistencia visual y tono seguro.",
            },
            "visual_profile": {
                "archetype": "editorial nocturna",
                "body_type": "athletic",
                "skin_tone": "olive",
                "eye_color": "hazel",
                "hair_color": "dark_brown",
                "hair_style": "soft_waves",
                "dominant_features": ["confident_gaze", "defined_jawline"],
                "wardrobe_styles": ["luxury_lingerie"],
                "visual_must_haves": ["soft_gold_lighting"],
                "visual_never_do": ["cartoon_style"],
            },
            "personality_profile": {
                "voice_tone": "seductive",
                "primary_traits": ["confident", "observant"],
                "secondary_traits": ["warm", "strategic"],
                "interaction_style": "Mantiene un tono directo, premium y consistente con la escena.",
                "axes": {
                    "formality": "medium",
                    "warmth": "high",
                    "dominance": "medium",
                    "provocation": "high",
                    "accessibility": "medium",
                },
            },
            "narrative_profile": {
                "archetype_summary": "Performer digital premium construida para hooks conversacionales y escenas editoriales.",
                "origin_story": "Nace como una identidad sintética optimizada para glamour nocturno y monetización escalable.",
                "motivations": ["grow_premium_audience", "protect_brand_consistency"],
                "interests": ["fashion", "nightlife"],
                "audience_role": "fantasy_guide",
                "conversational_hooks": ["after_hours_stories", "style_breakdowns"],
            },
            "operational_limits": {
                "allowed_content_modes": ["sfw", "sensual", "nsfw"],
                "hard_limits": hard_limits,
                "soft_limits": [
                    {
                        "code": "avoid_body_horror",
                        "label": "Avoid body horror aesthetics",
                        "severity": "soft",
                        "rationale": "Mantener consistencia aspiracional del personaje.",
                    }
                ],
                "escalation_triggers": ["unsafe_request", "identity_drift"],
            },
            "system5_slots": {
                "persona_summary": "Figura segura, elegante y provocadora con memoria de preferencias.",
                "greeting_style": "Abre con curiosidad segura y una invitacion breve.",
                "reply_style_keywords": ["flirty", "direct"],
                "memory_tags": ["style_preferences", "favorite_scenarios"],
                "prohibited_topics": ["illegal_content", "real_world_personal_data"],
                "upsell_style": "Escala hacia premium sin romper personaje.",
            },
            "traceability": {
                "source_issue_id": "DEV-7",
                "source_epic_id": "DEV-3",
                "contract_owner": "Codex",
                "future_systems_ready": ["system_2", "system_5"],
                "last_reviewed_at": timestamp,
            },
        }
    )


def build_expansion_payload(*, with_hard_limits: bool = True) -> dict:
    return {
        "expansion_summary": "Expansion inicial lista para generar una ficha tecnica narrativa y operativa estable.",
        "prompt_blueprint": "Identity blueprint optimized for visual consistency, emotional hooks and safe operational limits.",
        "assumptions": ["unit_test"],
        "technical_sheet_payload": build_technical_sheet(with_hard_limits=with_hard_limits).model_dump(mode="json"),
    }


def build_copilot_payload(*, supported_modes: list[str] | None = None) -> dict:
    return {
        "workflow_id": "copilot-editorial-v1",
        "base_model_id": "flux-schnell-v1",
        "node_ids": ["load_model", "ip_adapter_plus", "ksampler", "vae_decode"],
        "prompt_template": "Editorial nightlife portrait, premium lighting, identity-consistent facial features.",
        "negative_prompt": "low quality, anatomy drift, minors, body horror, extra limbs",
        "rationale": "Workflow preparado para glamour nocturno con control de identidad y sampler consumible.",
        "content_modes_supported": supported_modes or ["sfw", "sensual", "nsfw"],
    }


def test_runner_returns_succeeded_graph_state() -> None:
    result = run_agentic_brain("performer glam nocturna con tono seguro y premium")

    assert result.completion_status == CompletionStatus.SUCCEEDED
    assert result.final_technical_sheet_payload is not None
    assert result.copilot_recommendation is not None
    assert result.validation_result is not None
    assert result.validation_result.valid is True


def test_validator_rejects_missing_hard_limits() -> None:
    state = GraphState.model_validate(
        {
            "input_idea": "idea de prueba suficientemente larga",
            "attempt_count": 1,
            "max_attempts": 2,
            "expanded_context": build_expansion_payload(with_hard_limits=False),
            "copilot_recommendation": build_copilot_payload(),
        }
    )

    outcome = TechnicalSheetGraphValidator().validate(state)

    assert outcome.valid is False
    assert outcome.final_payload_consumable is False
    assert outcome.issues[0].code == "missing_hard_limits"


def test_graph_retries_after_validation_failure_and_recovers() -> None:
    settings = AgenticSettings(max_attempts=2)
    attempts = {"count": 0}

    def llm_factory(idea: str, critique_history: list[object], attempt_count: int) -> dict:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return build_expansion_payload(with_hard_limits=False)
        assert critique_history
        return build_expansion_payload(with_hard_limits=True)

    from vixenbliss_creator.agentic.adapters import FakeCopilotClient, FakeLLMClient

    brain = build_agentic_brain(
        settings=settings,
        llm_client=FakeLLMClient(factory=llm_factory),
        copilot_client=FakeCopilotClient(factory=lambda expansion: build_copilot_payload()),
    )

    result = brain.invoke(GraphState(input_idea="idea de prueba suficientemente larga"))

    assert attempts["count"] == 2
    assert result.completion_status == CompletionStatus.SUCCEEDED
    assert result.validation_result is not None
    assert result.validation_result.valid is True
    assert result.critique_history[0].code == "missing_hard_limits"


def test_graph_fails_when_retries_are_exhausted() -> None:
    settings = AgenticSettings(max_attempts=1)

    from vixenbliss_creator.agentic.adapters import FakeCopilotClient, FakeLLMClient

    brain = build_agentic_brain(
        settings=settings,
        llm_client=FakeLLMClient(factory=lambda idea, critique_history, attempt_count: build_expansion_payload(with_hard_limits=False)),
        copilot_client=FakeCopilotClient(factory=lambda expansion: build_copilot_payload()),
    )

    result = brain.invoke(GraphState(input_idea="idea de prueba suficientemente larga"))

    assert result.completion_status == CompletionStatus.FAILED
    assert "exhausted retries" in result.terminal_error_message
    assert result.final_technical_sheet_payload is None


def test_graph_caps_critique_history_before_failing() -> None:
    settings = AgenticSettings(max_attempts=5)

    class NoisyValidator:
        def validate(self, state: GraphState) -> ValidationOutcome:
            return ValidationOutcome(
                valid=False,
                issues=[
                    CritiqueIssue(
                        code=f"issue_{index}",
                        message=f"Issue number {index} is retryable.",
                        source_node="validator",
                    )
                    for index in range(5)
                ],
                final_payload_consumable=False,
            )

    from vixenbliss_creator.agentic.adapters import FakeCopilotClient, FakeLLMClient

    brain = build_agentic_brain(
        settings=settings,
        llm_client=FakeLLMClient(
            factory=lambda idea, critique_history, attempt_count: build_expansion_payload(with_hard_limits=True)
        ),
        copilot_client=FakeCopilotClient(factory=lambda expansion: build_copilot_payload(supported_modes=["sfw", "sensual", "nsfw"])),
        validator=NoisyValidator(),
    )

    result = brain.invoke(GraphState(input_idea="idea de prueba suficientemente larga"))

    assert result.completion_status == CompletionStatus.FAILED
    assert "exhausted retries" in result.terminal_error_message
    assert len(result.critique_history) == 20


def test_openai_adapter_parses_openai_compatible_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = AgenticSettings(
        llm_serverless_base_url="https://example.com/v1",
        llm_serverless_model="test-model",
        llm_serverless_api_key="secret",
    )

    captured: dict[str, object] = {}

    def fake_post(url: str, payload: dict, headers: dict[str, str]) -> dict:
        assert url == "https://example.com/v1/chat/completions"
        assert payload["model"] == "test-model"
        assert headers["Authorization"] == "Bearer secret"
        captured["payload"] = payload
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(build_expansion_payload())
                    }
                }
            ]
        }

    monkeypatch.setattr("vixenbliss_creator.agentic.adapters._json_post", fake_post)

    result = OpenAICompatibleLLMClient(settings).generate_expansion(
        idea="idea de prueba suficientemente larga",
        critique_history=[],
        attempt_count=1,
    )

    assert captured["payload"] is not None
    assert result.technical_sheet_payload.identity_core.display_name == "Velvet Ember"


def test_copilot_adapter_parses_http_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = AgenticSettings(
        comfyui_copilot_base_url="https://copilot.example.com/api",
        comfyui_copilot_api_key="secret",
        comfyui_copilot_path="/recommend",
    )

    captured: dict[str, object] = {}

    def fake_post(url: str, payload: dict, headers: dict[str, str]) -> dict:
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = payload
        return build_copilot_payload()

    monkeypatch.setattr("vixenbliss_creator.agentic.adapters._json_post", fake_post)

    result = ComfyUICopilotHTTPClient(settings).recommend_workflow(
        expansion=ExpansionResult.model_validate(build_expansion_payload())
    )

    assert captured["url"] == "https://copilot.example.com/api/recommend"
    assert result.workflow_id == "copilot-editorial-v1"
