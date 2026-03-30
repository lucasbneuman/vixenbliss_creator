from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from vixenbliss_creator.contracts.identity import TechnicalSheet

from .adapters import FakeCopilotClient, FakeLLMClient
from .config import AgenticSettings
from .graph import build_agentic_brain
from .models import CopilotRecommendation, GraphState


def _build_demo_technical_sheet(settings: AgenticSettings, idea: str) -> TechnicalSheet:
    timestamp = datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc).isoformat()
    alias_hint = idea.lower().replace(" ", "_")[:18] or "synthetic_muse"
    return TechnicalSheet.model_validate(
        {
            "schema_version": "1.0.0",
            "identity_core": {
                "display_name": "Velvet Ember",
                "fictional_age_years": 25,
                "locale": "es-AR",
                "primary_language": "spanish",
                "secondary_languages": ["english"],
                "tagline": f"Identidad premium derivada de {alias_hint} con foco visual coherente.",
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
                "archetype_summary": "Performer digital premium construida para escenas editoriales y hooks conversacionales claros.",
                "origin_story": "Nace como una identidad sintética optimizada para glamour nocturno, consistencia visual y monetización escalable.",
                "motivations": ["grow_premium_audience", "protect_brand_consistency"],
                "interests": ["fashion", "nightlife"],
                "audience_role": "fantasy_guide",
                "conversational_hooks": ["after_hours_stories", "style_breakdowns"],
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
                "persona_summary": "Figura segura, elegante y provocadora con memoria de preferencias y tono premium.",
                "greeting_style": "Abre con curiosidad segura y una invitacion breve.",
                "reply_style_keywords": ["flirty", "direct"],
                "memory_tags": ["style_preferences", "favorite_scenarios"],
                "prohibited_topics": ["illegal_content", "real_world_personal_data"],
                "upsell_style": "Escala desde complicidad ligera hacia premium sin romper personaje.",
            },
            "traceability": {
                "source_issue_id": settings.source_issue_id,
                "source_epic_id": settings.source_epic_id,
                "contract_owner": settings.contract_owner,
                "future_systems_ready": ["system_2", "system_5"],
                "last_reviewed_at": timestamp,
            },
        }
    )


def _build_demo_recommendation() -> CopilotRecommendation:
    return CopilotRecommendation.model_validate(
        {
            "workflow_id": "copilot-editorial-v1",
            "base_model_id": "flux-schnell-v1",
            "node_ids": ["load_model", "ip_adapter_plus", "ksampler", "vae_decode"],
            "prompt_template": "Editorial nightlife portrait, premium lighting, identity-consistent facial features.",
            "negative_prompt": "low quality, anatomy drift, minors, body horror, extra limbs",
            "rationale": "Workflow preparado para glamour nocturno con control de identidad y sampler consumible.",
            "content_modes_supported": ["sfw", "sensual", "nsfw"],
        }
    )


def run_agentic_brain(idea: str, settings: AgenticSettings | None = None) -> GraphState:
    settings = settings or AgenticSettings.from_env()
    technical_sheet = _build_demo_technical_sheet(settings, idea)
    llm = FakeLLMClient(
        factory=lambda current_idea, critique_history, attempt_count: {
            "expansion_summary": f"Expansion attempt {attempt_count} for: {current_idea}",
            "prompt_blueprint": "Identity blueprint optimized for visual consistency, emotional hooks and safe operational limits.",
            "assumptions": ["default_demo_runner"],
            "technical_sheet_payload": technical_sheet.model_dump(mode="json"),
        }
    )
    copilot = FakeCopilotClient(sequence=[_build_demo_recommendation()])
    brain = build_agentic_brain(settings=settings, llm_client=llm, copilot_client=copilot)
    seed_state = GraphState(input_idea=idea, max_attempts=settings.max_attempts)
    return brain.invoke(seed_state)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the VixenBliss agentic brain demo.")
    parser.add_argument("--idea", required=True, help="Natural-language idea to transform into GraphState.")
    args = parser.parse_args()

    result = run_agentic_brain(args.idea)
    print(json.dumps(result.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
