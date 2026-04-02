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
from vixenbliss_creator.agentic.models import (
    CompletionStatus,
    CreationMode,
    CritiqueDomain,
    CritiqueIssue,
    ExpansionResult,
    GraphState,
    ValidationOutcome,
)
from vixenbliss_creator.agentic.runner import run_agentic_brain
from vixenbliss_creator.agentic.validator import TechnicalSheetGraphValidator
from vixenbliss_creator.contracts.identity import TechnicalSheet


def build_technical_sheet(
    *,
    with_hard_limits: bool = True,
    vertical: str = "lifestyle",
    style: str = "premium",
    archetype: str = "luxury_muse",
    speech_style: str = "refined",
    sarcasm: str = "medium",
    fan_relationship_style: str = "aspirational_muse",
) -> TechnicalSheet:
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
            "identity_metadata": {
                "avatar_id": "avatar_velvet_ember",
                "category": "lifestyle_premium" if vertical == "lifestyle" else "adult_creator",
                "vertical": vertical,
                "style": style,
                "occupation_or_content_basis": "luxury lifestyle creator" if vertical == "lifestyle" else "premium digital performer",
            },
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
                "archetype": archetype,
                "voice_tone": "authoritative" if vertical == "lifestyle" else "seductive",
                "primary_traits": ["confident", "observant"],
                "secondary_traits": ["warm", "strategic"],
                "interaction_style": "Mantiene un tono directo, premium y consistente con la escena.",
                "axes": {
                    "dominance": "medium" if vertical == "lifestyle" else "high",
                    "warmth": "high",
                    "playfulness": "medium",
                    "mystery": "high",
                    "flirtiness": "high",
                    "intelligence": "high",
                    "sarcasm": sarcasm,
                },
                "communication_style": {
                    "speech_style": speech_style,
                    "message_length": "medium",
                    "emoji_usage": "moderate",
                    "emoji_style": "sparkles",
                    "punctuation_style": "polished",
                },
                "social_behavior": {
                    "fan_relationship_style": fan_relationship_style,
                    "attention_strategy": "balanced",
                    "response_energy": "medium",
                    "jealousy_play": "light",
                },
            },
            "narrative_profile": {
                "archetype_summary": "Performer digital premium construida para hooks conversacionales y escenas editoriales.",
                "origin_story": "Nace como una identidad sintetica optimizada para glamour nocturno y monetizacion escalable.",
                "motivations": ["grow_premium_audience", "protect_brand_consistency"],
                "interests": ["fashion", "nightlife"],
                "audience_role": "aspirational" if vertical == "lifestyle" else "fantasy_guide",
                "conversational_hooks": ["after_hours_stories", "style_breakdowns"],
                "minimal_viable_profile": {
                    "origin": "Construyo una presencia digital premium preparada para fantasia aspiracional y consistencia comercial.",
                    "interests": ["fashion", "nightlife"],
                    "daily_life": "Alterna sesiones de contenido curado, fitness suave y una presencia social muy medida.",
                    "motivation": "Convertir estilo y presencia en una marca rentable y duradera.",
                    "relationship_with_fans": "Se acerca con calidez medida y mantiene una sensacion de exclusividad controlada.",
                },
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
                "field_traces": [
                    {
                        "field_path": "metadata.vertical",
                        "origin": "manual",
                        "source_text": "operator_request",
                        "confidence": 1.0,
                        "rationale": "El operador fijo la vertical.",
                    },
                    {
                        "field_path": "metadata.style",
                        "origin": "manual" if style == "glam" else "inferred",
                        "source_text": "operator_request",
                        "confidence": 0.9,
                        "rationale": "Runner de test.",
                    },
                    {
                        "field_path": "archetype",
                        "origin": "manual" if archetype == "dominant_queen" else "inferred",
                        "source_text": "operator_request",
                        "confidence": 0.9,
                        "rationale": "Runner de test.",
                    },
                    {
                        "field_path": "communication_style.speech_style",
                        "origin": "manual" if speech_style == "casual" else "inferred",
                        "source_text": "operator_request",
                        "confidence": 0.9,
                        "rationale": "Runner de test.",
                    },
                    {
                        "field_path": "personality_axes.sarcasm",
                        "origin": "manual" if sarcasm == "high" else "inferred",
                        "source_text": "operator_request",
                        "confidence": 0.9,
                        "rationale": "Runner de test.",
                    },
                ],
            },
        }
    )


def build_expansion_payload(
    *,
    with_hard_limits: bool = True,
    vertical: str = "lifestyle",
    style: str = "premium",
    archetype: str = "luxury_muse",
    speech_style: str = "refined",
    sarcasm: str = "medium",
    fan_relationship_style: str = "aspirational_muse",
    missing_fields: list[str] | None = None,
) -> dict:
    technical_sheet = build_technical_sheet(
        with_hard_limits=with_hard_limits,
        vertical=vertical,
        style=style,
        archetype=archetype,
        speech_style=speech_style,
        sarcasm=sarcasm,
        fan_relationship_style=fan_relationship_style,
    )
    manual_fields = [
        trace.field_path for trace in technical_sheet.traceability.field_traces if trace.origin == "manual"
    ]
    inferred_fields = [
        trace.field_path for trace in technical_sheet.traceability.field_traces if trace.origin != "manual"
    ]
    return {
        "expansion_summary": "Expansion inicial lista para construir identidad estructurada y ficha tecnica operativa.",
        "prompt_blueprint": "Identity blueprint optimized for identity constraints, coherent personality, narrative and safe operational limits.",
        "assumptions": ["unit_test"],
        "normalized_constraints": {
            "category": technical_sheet.identity_metadata.category,
            "vertical": technical_sheet.identity_metadata.vertical,
            "style": technical_sheet.identity_metadata.style,
            "occupation_or_content_basis": technical_sheet.identity_metadata.occupation_or_content_basis,
            "archetype": technical_sheet.personality_profile.archetype,
            "speech_style": technical_sheet.personality_profile.communication_style.speech_style,
            "voice_tone": technical_sheet.personality_profile.voice_tone,
            "explicitly_defined_fields": manual_fields,
            "source_excerpt": "input de prueba",
        },
        "identity_draft": {
            "metadata": technical_sheet.identity_metadata.model_dump(mode="json"),
            "name": technical_sheet.identity_core.display_name,
            "archetype": technical_sheet.personality_profile.archetype,
            "personality_axes": technical_sheet.personality_profile.axes.model_dump(mode="json"),
            "communication_style": technical_sheet.personality_profile.communication_style.model_dump(mode="json"),
            "social_behavior": technical_sheet.personality_profile.social_behavior.model_dump(mode="json"),
            "narrative_minimal": technical_sheet.narrative_profile.minimal_viable_profile.model_dump(mode="json"),
            "field_traces": [trace.model_dump(mode="json") for trace in technical_sheet.traceability.field_traces],
        },
        "completion_report": {
            "manually_defined_fields": manual_fields,
            "inferred_fields": inferred_fields,
            "missing_fields": missing_fields or [],
        },
        "technical_sheet_payload": technical_sheet.model_dump(mode="json"),
    }


def build_copilot_payload(*, supported_modes: list[str] | None = None) -> dict:
    return {
        "workflow_id": "copilot-editorial-v2",
        "base_model_id": "flux-schnell-v1",
        "node_ids": ["load_model", "ip_adapter_plus", "ksampler", "vae_decode"],
        "prompt_template": "Editorial nightlife portrait aligned with identity metadata and communication style.",
        "negative_prompt": "low quality, anatomy drift, minors, body horror, extra limbs",
        "rationale": "Workflow preparado para glamour premium con control de identidad.",
        "content_modes_supported": supported_modes or ["sfw", "sensual", "nsfw"],
    }


def test_runner_returns_succeeded_graph_state() -> None:
    result = run_agentic_brain("Creá un avatar nuevo para lifestyle premium")

    assert result.completion_status == CompletionStatus.SUCCEEDED
    assert result.creation_mode == CreationMode.AUTOMATIC
    assert result.identity_draft is not None
    assert result.final_technical_sheet_payload is not None
    assert result.validation_result is not None
    assert result.validation_result.valid is True


def test_validator_rejects_missing_hard_limits() -> None:
    state = GraphState.model_validate(
        {
            "input_idea": "idea de prueba suficientemente larga",
            "attempt_count": 1,
            "max_attempts": 2,
            "identity_draft": build_expansion_payload(with_hard_limits=False)["identity_draft"],
            "expanded_context": build_expansion_payload(with_hard_limits=False),
            "manually_defined_fields": ["metadata.vertical"],
            "inferred_fields": ["metadata.style"],
            "copilot_recommendation": build_copilot_payload(),
        }
    )

    outcome = TechnicalSheetGraphValidator().validate(state)

    assert outcome.valid is False
    assert outcome.final_payload_consumable is False
    assert outcome.issues[0].code == "missing_hard_limits"
    assert outcome.issues[0].domain == CritiqueDomain.OPERATIONAL_LIMITS


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
                        source_node="validate_final_payload",
                        target_node="complete_identity_profile",
                    )
                    for index in range(5)
                ],
                final_payload_consumable=False,
            )

    from vixenbliss_creator.agentic.adapters import FakeCopilotClient, FakeLLMClient

    brain = build_agentic_brain(
        settings=settings,
        llm_client=FakeLLMClient(factory=lambda idea, critique_history, attempt_count: build_expansion_payload(with_hard_limits=True)),
        copilot_client=FakeCopilotClient(factory=lambda expansion: build_copilot_payload()),
        validator=NoisyValidator(),
    )

    result = brain.invoke(GraphState(input_idea="idea de prueba suficientemente larga"))

    assert result.completion_status == CompletionStatus.FAILED
    assert "exhausted retries" in result.terminal_error_message
    assert len(result.critique_history) == 20


def test_automatic_mode_infers_vertical_profile() -> None:
    result = run_agentic_brain("Creá un avatar nuevo para lifestyle premium")

    assert result.creation_mode == CreationMode.AUTOMATIC
    assert result.identity_draft is not None
    assert result.identity_draft.metadata.vertical == "lifestyle"
    assert result.final_technical_sheet_payload.identity_metadata.style == "premium"


def test_partial_manual_attributes_keep_traceability() -> None:
    result = run_agentic_brain("Quiero alguien sarcástica y casual, el resto automático")

    assert result.creation_mode == CreationMode.SEMI_AUTOMATIC
    assert "communication_style.speech_style" in result.manually_defined_fields
    assert "personality_axes.sarcasm" in result.manually_defined_fields
    trace_map = result.identity_draft.trace_map()
    assert trace_map["communication_style.speech_style"].origin == "manual"
    assert trace_map["personality_axes.sarcasm"].origin == "manual"


def test_archetype_manual_case_completes_remaining_fields() -> None:
    result = run_agentic_brain("Definime solo el arquetipo, yo quiero dominant queen")

    assert result.creation_mode == CreationMode.HYBRID_BY_ATTRIBUTE
    assert result.identity_draft.archetype == "dominant_queen"
    assert not result.missing_fields
    assert "archetype" in result.manually_defined_fields


def test_category_and_style_can_be_manual_while_narrative_is_generated() -> None:
    result = run_agentic_brain("Quiero elegir categoría y estilo, pero la narrativa hacela sola")

    assert result.creation_mode == CreationMode.HYBRID_BY_ATTRIBUTE
    assert "metadata.category" in result.manually_defined_fields
    assert "metadata.style" in result.manually_defined_fields
    assert result.identity_draft.narrative_minimal.relationship_with_fans


def test_validator_blocks_incoherent_vertical_personality_combination() -> None:
    state = GraphState.model_validate(
        {
            "input_idea": "idea de prueba suficientemente larga",
            "attempt_count": 1,
            "max_attempts": 2,
            "identity_draft": build_expansion_payload(
                with_hard_limits=True,
                vertical="lifestyle",
                archetype="dominant_queen",
                sarcasm="very_high",
                speech_style="casual",
                fan_relationship_style="commanding_presence",
            )["identity_draft"],
            "expanded_context": build_expansion_payload(
                with_hard_limits=True,
                vertical="lifestyle",
                archetype="dominant_queen",
                sarcasm="very_high",
                speech_style="casual",
                fan_relationship_style="commanding_presence",
            ),
            "manually_defined_fields": ["metadata.vertical", "archetype", "personality_axes.sarcasm"],
            "inferred_fields": ["metadata.style"],
            "copilot_recommendation": build_copilot_payload(),
        }
    )

    outcome = TechnicalSheetGraphValidator().validate(state)

    assert outcome.valid is False
    issue_codes = {issue.code for issue in outcome.issues}
    assert "vertical_business_violation" in issue_codes
    assert {"premium_personality_conflict", "style_behavior_conflict"} & issue_codes


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
    assert result.identity_draft.metadata.style == "premium"
    assert result.technical_sheet_payload.identity_core.display_name == "Velvet Ember"


def test_settings_can_resolve_openai_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_SERVERLESS_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_SERVERLESS_API_KEY", raising=False)
    monkeypatch.delenv("LLM_SERVERLESS_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    settings = AgenticSettings.from_env()

    assert settings.resolved_llm_base_url == "https://api.openai.com/v1"
    assert settings.resolved_llm_api_key == "openai-secret"
    assert settings.resolved_llm_model == "gpt-4o-mini"


def test_openai_adapter_uses_openai_fallback_when_serverless_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = AgenticSettings(
        openai_api_key="openai-secret",
        openai_model="gpt-4o-mini",
    )

    captured: dict[str, object] = {}

    def fake_post(url: str, payload: dict, headers: dict[str, str]) -> dict:
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
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

    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["payload"]["model"] == "gpt-4o-mini"
    assert captured["headers"]["Authorization"] == "Bearer openai-secret"
    assert result.identity_draft.metadata.category == "lifestyle_premium"


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
    assert result.workflow_id == "copilot-editorial-v2"
