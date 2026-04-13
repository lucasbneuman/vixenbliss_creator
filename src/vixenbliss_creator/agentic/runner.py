from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from .adapters import FakeCopilotClient, FakeLLMClient, OpenAICompatibleLLMClient
from .config import AgenticSettings
from .graph import build_agentic_brain
from .models import CopilotRecommendation, GraphState
from .naming import resolve_display_name
from vixenbliss_creator.contracts.identity import (
    ArchetypeCode,
    CommunicationStyleProfile,
    CreationCategory,
    FieldTrace,
    IdentityMetadata,
    IdentityStyle,
    JealousyPlayLevel,
    MessageLength,
    NarrativeMinimalProfile,
    PersonalityAxes,
    ResponseEnergy,
    SocialBehaviorProfile,
    SpeechStyle,
    TechnicalSheet,
)


def _scenario_from_idea(idea: str) -> dict[str, object]:
    normalized = idea.lower()
    lifestyle = "lifestyle" in normalized
    premium = "premium" in normalized
    dominant = "dominant queen" in normalized or "dominante" in normalized
    sarcastic = "sarc" in normalized
    casual = "casual" in normalized
    choose_category = "categoría" in normalized or "categoria" in normalized
    choose_style = "estilo" in normalized

    style = IdentityStyle.PREMIUM if premium or lifestyle else IdentityStyle.GLAM
    vertical = "lifestyle" if lifestyle else "adult_entertainment"
    category = CreationCategory.LIFESTYLE_PREMIUM if lifestyle else CreationCategory.ADULT_CREATOR
    archetype = ArchetypeCode.DOMINANT_QUEEN if dominant else (ArchetypeCode.LUXURY_MUSE if lifestyle else ArchetypeCode.PLAYFUL_TEASE)
    speech_style = SpeechStyle.CASUAL if casual else (SpeechStyle.REFINED if lifestyle else SpeechStyle.GLAM)
    sarcasm = "high" if sarcastic else "medium"
    fan_relationship = "aspirational_muse" if lifestyle else "curated_distance"
    manual_fields = []
    if lifestyle:
        manual_fields.append("metadata.vertical")
    if premium:
        manual_fields.append("metadata.style")
    if choose_category:
        manual_fields.append("metadata.category")
    if choose_style and "metadata.style" not in manual_fields:
        manual_fields.append("metadata.style")
    if dominant:
        manual_fields.append("archetype")
    if casual:
        manual_fields.append("communication_style.speech_style")
    if sarcastic:
        manual_fields.append("personality_axes.sarcasm")

    display_name = resolve_display_name(idea)

    return {
        "metadata": {
            "avatar_id": None,
            "category": category.value,
            "vertical": vertical,
            "style": style.value,
            "occupation_or_content_basis": "luxury lifestyle creator" if lifestyle else "premium digital performer",
        },
        "name": display_name,
        "archetype": archetype.value,
        "personality_axes": {
            "dominance": "medium" if lifestyle else "high",
            "warmth": "high",
            "playfulness": "medium" if lifestyle else "high",
            "mystery": "high",
            "flirtiness": "high",
            "intelligence": "high" if lifestyle else "medium",
            "sarcasm": sarcasm,
        },
        "communication_style": {
            "speech_style": speech_style.value,
            "message_length": "medium",
            "emoji_usage": "moderate",
            "emoji_style": "sparkles",
            "punctuation_style": "polished" if lifestyle else "expressive",
        },
        "social_behavior": {
            "fan_relationship_style": fan_relationship,
            "attention_strategy": "balanced" if lifestyle else "exclusive",
            "response_energy": "medium" if lifestyle else "high",
            "jealousy_play": "light",
        },
        "narrative_minimal": {
            "origin": "Built as a premium synthetic identity for repeatable scenes, brand consistency, and aspirational fantasy.",
            "interests": ["fashion", "hospitality"] if lifestyle else ["fashion", "nightlife"],
            "daily_life": "Balances curated shoots, aesthetic routines, and tightly controlled audience-facing moments.",
            "motivation": "Turn a consistent digital presence into a memorable and profitable brand.",
            "relationship_with_fans": "Builds closeness with measured warmth while preserving exclusivity and control.",
        },
        "manual_fields": manual_fields,
        "inferred_fields": [
            field_path
            for field_path in (
                "metadata.category",
                "metadata.occupation_or_content_basis",
                "social_behavior.fan_relationship_style",
                "narrative_minimal.relationship_with_fans",
            )
            if field_path not in manual_fields
        ],
    }


def _build_demo_technical_sheet(settings: AgenticSettings, scenario: dict[str, object]) -> TechnicalSheet:
    timestamp = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc).isoformat()
    return TechnicalSheet.model_validate(
        {
            "schema_version": "1.0.0",
            "identity_metadata": scenario["metadata"],
            "identity_core": {
                "display_name": scenario["name"],
                "fictional_age_years": 25,
                "locale": "es-AR",
                "primary_language": "spanish",
                "secondary_languages": ["english"],
                "tagline": "Synthetic premium identity prepared for System 1 handoff and downstream content systems.",
            },
            "visual_profile": {
                "archetype": "editorial nocturna",
                "body_type": "athletic",
                "skin_tone": "olive",
                "eye_color": "hazel",
                "hair_color": "dark_brown",
                "hair_style": "soft_waves",
                "dominant_features": ["confident_gaze", "defined_jawline"],
                "wardrobe_styles": ["luxury_lingerie", "nightlife_glam"],
                "visual_must_haves": ["soft_gold_lighting"],
                "visual_never_do": ["cartoon_style"],
            },
            "personality_profile": {
                "archetype": scenario["archetype"],
                "voice_tone": "authoritative" if scenario["metadata"]["vertical"] == "lifestyle" else "seductive",
                "primary_traits": ["confident", "observant"],
                "secondary_traits": ["warm", "strategic"],
                "interaction_style": f"Maintains a clear, emotionally controlled, and commercially coherent presence for the {scenario['metadata']['vertical']} vertical.",
                "axes": scenario["personality_axes"],
                "communication_style": scenario["communication_style"],
                "social_behavior": scenario["social_behavior"],
            },
            "narrative_profile": {
                "archetype_summary": "Premium performer built to sustain a clear voice and commercially consistent identity behavior.",
                "origin_story": "Created as a synthetic identity optimized for style, coherence, and scalable monetization.",
                "motivations": ["grow_premium_audience", "protect_brand_consistency"],
                "interests": scenario["narrative_minimal"]["interests"],
                "audience_role": "aspirational" if scenario["metadata"]["vertical"] == "lifestyle" else "fantasy_guide",
                "conversational_hooks": ["after_hours_stories", "style_breakdowns"],
                "minimal_viable_profile": scenario["narrative_minimal"],
            },
            "operational_limits": {
                "allowed_content_modes": ["sfw", "sensual", "nsfw"],
                "hard_limits": [
                    {
                        "code": "no_minors",
                        "label": "No underage framing",
                        "severity": "hard",
                        "rationale": "El personaje siempre se representa como adulto ficticio.",
                    }
                ],
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
                "persona_summary": f"{scenario['name']} is a synthetic identity built for System 1 with a {scenario['metadata']['style']} tone, {scenario['metadata']['vertical']} positioning, and a {scenario['archetype']} conversational archetype.",
                "greeting_style": "Opens with confident curiosity, light invitation, and immediate emotional presence.",
                "reply_style_keywords": ["flirty", "direct", "premium"],
                "memory_tags": ["style_preferences", "favorite_scenarios", "boundaries", "upsell_readiness"],
                "prohibited_topics": ["illegal_content", "real_world_personal_data"],
                "upsell_style": "Escalates from playful intimacy into premium offers without breaking character consistency.",
                "conversation_openers": [
                    "What kind of mood are you in tonight?",
                    "Do you want something playful, soft, or more intense?",
                    "Tell me what kind of attention you are craving right now.",
                ],
                "emotional_triggers": ["feeling desired", "exclusive attention", "playful validation", "confident reassurance"],
                "fantasy_pillars": ["seductive teasing", "exclusive closeness", "glamour", "guided escalation"],
                "relationship_progression": "Moves from warm curiosity to trusted intimacy, then into premium exclusivity.",
                "tone_guardrails": ["never sounds generic", "never breaks confidence", "never loses flirt tension"],
            },
            "traceability": {
                "source_issue_id": settings.source_issue_id,
                "source_epic_id": settings.source_epic_id,
                "contract_owner": settings.contract_owner,
                "future_systems_ready": ["system_2", "system_5"],
                "last_reviewed_at": timestamp,
                "field_traces": [
                    {
                        "field_path": field_path,
                        "origin": "manual" if field_path in scenario["manual_fields"] else "inferred",
                        "source_text": "runner_demo",
                        "confidence": 1.0,
                        "rationale": "Runner determinista para evidencia minima.",
                    }
                    for field_path in [*scenario["manual_fields"], *scenario["inferred_fields"]]
                ],
            },
        }
    )


def _build_demo_expansion_payload(settings: AgenticSettings, idea: str) -> dict:
    scenario = _scenario_from_idea(idea)
    technical_sheet = _build_demo_technical_sheet(settings, scenario)
    all_traces = technical_sheet.traceability.field_traces
    return {
        "expansion_summary": f"Identity expansion completed for scenario derived from: {idea}",
        "prompt_blueprint": "Structured identity blueprint optimized for constraints, coherence, technical translation and safe operational limits.",
        "assumptions": ["default_demo_runner", "system1_personality_mode"],
        "normalized_constraints": {
            "category": technical_sheet.identity_metadata.category,
            "vertical": technical_sheet.identity_metadata.vertical,
            "style": technical_sheet.identity_metadata.style,
            "occupation_or_content_basis": technical_sheet.identity_metadata.occupation_or_content_basis,
            "archetype": technical_sheet.personality_profile.archetype,
            "speech_style": technical_sheet.personality_profile.communication_style.speech_style,
            "voice_tone": technical_sheet.personality_profile.voice_tone,
            "explicitly_defined_fields": scenario["manual_fields"],
            "source_excerpt": idea,
        },
        "identity_draft": {
            "metadata": technical_sheet.identity_metadata.model_dump(mode="json"),
            "name": technical_sheet.identity_core.display_name,
            "archetype": technical_sheet.personality_profile.archetype,
            "personality_axes": technical_sheet.personality_profile.axes.model_dump(mode="json"),
            "communication_style": technical_sheet.personality_profile.communication_style.model_dump(mode="json"),
            "social_behavior": technical_sheet.personality_profile.social_behavior.model_dump(mode="json"),
            "narrative_minimal": technical_sheet.narrative_profile.minimal_viable_profile.model_dump(mode="json"),
            "field_traces": [trace.model_dump(mode="json") for trace in all_traces],
        },
        "completion_report": {
            "manually_defined_fields": scenario["manual_fields"],
            "inferred_fields": scenario["inferred_fields"],
            "missing_fields": [],
        },
        "technical_sheet_payload": technical_sheet.model_dump(mode="json"),
    }


def _build_demo_recommendation() -> CopilotRecommendation:
    return CopilotRecommendation.model_validate(
        {
            "stage": "s1_identity_image",
            "workflow_id": "lora-dataset-ipadapter-batch",
            "workflow_version": "2026-04-08",
            "recommended_workflow_family": "flux_lora_dataset_reference",
            "base_model_id": "flux-schnell-v1",
            "required_nodes": ["load_model", "ip_adapter_plus", "ksampler", "vae_decode"],
            "optional_nodes": ["face_detector", "face_detailer"],
            "model_hints": ["flux", "ipadapter-face", "impact-pack", "batch-dataset"],
            "prompt_template": (
                "Photorealistic adult dataset workflow for LoRA training with deterministic angle coverage, "
                "full-body emphasis, real-person skin texture, and identity-preserving editorial realism."
            ),
            "negative_prompt": (
                "low quality, anatomy drift, minors, body horror, extra limbs, cgi, 3d, illustration, anime, "
                "plastic skin, mannequin, watermark, text"
            ),
            "reasoning_summary": "Workflow preparado para dataset LoRA realista con cobertura de shot plan y continuidad facial.",
            "risk_flags": ["identity_drift", "face_confidence_low", "dataset_coverage_gap"],
            "compatibility_notes": ["Approved for System 1 LoRA dataset generation."],
            "content_modes_supported": ["sfw", "sensual", "nsfw"],
            "registry_source": "demo_runner",
        }
    )


def run_agentic_brain(idea: str, settings: AgenticSettings | None = None) -> GraphState:
    settings = settings or AgenticSettings.from_env()
    llm = FakeLLMClient(
        factory=lambda current_idea, critique_history, attempt_count: _build_demo_expansion_payload(settings, current_idea)
    )
    copilot = FakeCopilotClient(factory=lambda expansion: _build_demo_recommendation())
    brain = build_agentic_brain(settings=settings, llm_client=llm, copilot_client=copilot)
    seed_state = GraphState(input_idea=idea, max_attempts=settings.max_attempts)
    return brain.invoke(seed_state)


def run_agentic_brain_with_real_llm(idea: str, settings: AgenticSettings | None = None) -> GraphState:
    settings = settings or AgenticSettings.from_env()
    llm = OpenAICompatibleLLMClient(settings)
    copilot = FakeCopilotClient(factory=lambda expansion: _build_demo_recommendation())
    brain = build_agentic_brain(settings=settings, llm_client=llm, copilot_client=copilot)
    seed_state = GraphState(input_idea=idea, max_attempts=settings.max_attempts)
    return brain.invoke(seed_state)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the VixenBliss agentic brain demo.")
    parser.add_argument("--idea", required=True, help="Natural-language idea to transform into GraphState.")
    parser.add_argument(
        "--real-llm",
        action="store_true",
        help="Use the real OpenAI-compatible/OpenAI LLM adapter and keep Copilot deterministic.",
    )
    args = parser.parse_args()

    result = run_agentic_brain_with_real_llm(args.idea) if args.real_llm else run_agentic_brain(args.idea)
    print(json.dumps(result.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
