from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable
from urllib import error, parse, request

from .config import AgenticSettings
from .models import CopilotRecommendation, CritiqueIssue, ExpansionResult
from vixenbliss_creator.contracts.identity import (
    ArchetypeCode,
    AttentionStrategy,
    AudienceRole,
    CreationCategory,
    EmojiUsage,
    FanRelationshipStyle,
    FieldTrace,
    IdentityStyle,
    JealousyPlayLevel,
    MessageLength,
    PunctuationStyle,
    ResponseEnergy,
    SpeechStyle,
    TechnicalSheet,
    TraitScale,
    Vertical,
    VoiceTone,
)


def _json_post(url: str, payload: dict, headers: dict[str, str]) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP error calling {url}: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error calling {url}: {exc.reason}") from exc
    return json.loads(raw)


def _enum_values(enum_type: type) -> list[str]:
    return [member.value for member in enum_type]


def _build_field_traces(payload: dict, idea: str) -> list[dict]:
    completion_report = payload.get("completion_report", {}) or {}
    normalized_constraints = payload.get("normalized_constraints", {}) or {}
    explicit = normalized_constraints.get("explicitly_defined_fields", []) or completion_report.get("manually_defined_fields", [])
    manual_fields = [field for field in list(dict.fromkeys(explicit or completion_report.get("manually_defined_fields", []))) if field != "field.path"]
    inferred_fields = [field for field in list(dict.fromkeys(completion_report.get("inferred_fields", []))) if field != "field.path"]
    if not inferred_fields:
        inferred_fields = [
            "metadata.category",
            "metadata.occupation_or_content_basis",
            "archetype",
            "communication_style.speech_style",
            "voice_tone",
        ]
    traces: list[dict] = []
    for field_path in manual_fields:
        traces.append(
            {
                "field_path": field_path,
                "origin": "manual",
                "source_text": idea,
                "confidence": 1.0,
                "rationale": "Campo detectado como explicito en la instruccion del operador.",
            }
        )
    for field_path in inferred_fields:
        if field_path in manual_fields:
            continue
        traces.append(
            {
                "field_path": field_path,
                "origin": "inferred",
                "source_text": idea,
                "confidence": 0.8,
                "rationale": "Campo completado por inferencia para cerrar la identidad.",
            }
        )
    return traces


def _build_technical_sheet_from_identity(payload: dict, settings: AgenticSettings, idea: str) -> dict:
    normalized_constraints = payload.get("normalized_constraints", {}) or {}
    identity_draft = payload.get("identity_draft", {}) or {}
    metadata = identity_draft.get("metadata", {}) or {}
    communication_style = identity_draft.get("communication_style", {}) or {}
    social_behavior = identity_draft.get("social_behavior", {}) or {}
    personality_axes = identity_draft.get("personality_axes", {}) or {}
    narrative_minimal = identity_draft.get("narrative_minimal", {}) or {}
    field_traces = identity_draft.get("field_traces") or _build_field_traces(payload, idea)

    vertical = metadata.get("vertical") or normalized_constraints.get("vertical") or Vertical.ADULT_ENTERTAINMENT.value
    style = metadata.get("style") or normalized_constraints.get("style") or IdentityStyle.EDITORIAL.value
    occupation = (
        metadata.get("occupation_or_content_basis")
        or normalized_constraints.get("occupation_or_content_basis")
        or "premium digital performer"
    )
    archetype = identity_draft.get("archetype") or normalized_constraints.get("archetype") or ArchetypeCode.PLAYFUL_TEASE.value
    voice_tone = normalized_constraints.get("voice_tone") or (VoiceTone.AUTHORITATIVE.value if vertical == Vertical.LIFESTYLE.value else VoiceTone.SEDUCTIVE.value)
    display_name = identity_draft.get("name") or "Velvet Ember"
    interests = narrative_minimal.get("interests") or ["fashion", "nightlife"]

    return {
        "schema_version": "1.0.0",
        "identity_metadata": {
            "avatar_id": metadata.get("avatar_id"),
            "category": metadata.get("category") or normalized_constraints.get("category") or CreationCategory.ADULT_CREATOR.value,
            "vertical": vertical,
            "style": style,
            "occupation_or_content_basis": occupation,
        },
        "identity_core": {
            "display_name": display_name,
            "fictional_age_years": 25,
            "locale": "es-AR",
            "primary_language": "spanish",
            "secondary_languages": ["english"],
            "tagline": f"Identidad sintetica de estilo {style} preparada para Sistema 1 y consumo posterior.",
        },
        "visual_profile": {
            "archetype": "editorial nocturna" if vertical != Vertical.LIFESTYLE.value else "luxury lifestyle portrait",
            "body_type": "athletic",
            "skin_tone": "olive",
            "eye_color": "hazel",
            "hair_color": "dark_brown",
            "hair_style": "soft_waves",
            "dominant_features": ["confident_gaze", "defined_jawline"],
            "wardrobe_styles": ["luxury_lingerie"] if vertical != Vertical.LIFESTYLE.value else ["premium_minimalist", "luxury_resort"],
            "visual_must_haves": ["soft_gold_lighting"],
            "visual_never_do": ["cartoon_style"],
        },
        "personality_profile": {
            "archetype": archetype,
            "voice_tone": voice_tone,
            "primary_traits": ["confident", "observant"],
            "secondary_traits": ["warm", "strategic"],
            "interaction_style": "Mantiene una presencia clara, consistente y alineada con la vertical comercial elegida.",
            "axes": {
                "dominance": personality_axes.get("dominance", TraitScale.MEDIUM.value),
                "warmth": personality_axes.get("warmth", TraitScale.HIGH.value),
                "playfulness": personality_axes.get("playfulness", TraitScale.MEDIUM.value),
                "mystery": personality_axes.get("mystery", TraitScale.MEDIUM.value),
                "flirtiness": personality_axes.get("flirtiness", TraitScale.MEDIUM.value),
                "intelligence": personality_axes.get("intelligence", TraitScale.HIGH.value),
                "sarcasm": personality_axes.get("sarcasm", TraitScale.LOW.value),
            },
            "communication_style": {
                "speech_style": communication_style.get("speech_style", SpeechStyle.REFINED.value),
                "message_length": communication_style.get("message_length", MessageLength.MEDIUM.value),
                "emoji_usage": communication_style.get("emoji_usage", EmojiUsage.LOW.value),
                "emoji_style": communication_style.get("emoji_style"),
                "punctuation_style": communication_style.get("punctuation_style", PunctuationStyle.POLISHED.value),
            },
            "social_behavior": {
                "fan_relationship_style": social_behavior.get("fan_relationship_style", FanRelationshipStyle.ASPIRATIONAL_MUSE.value),
                "attention_strategy": social_behavior.get("attention_strategy", AttentionStrategy.BALANCED.value),
                "response_energy": social_behavior.get("response_energy", ResponseEnergy.MEDIUM.value),
                "jealousy_play": social_behavior.get("jealousy_play", JealousyPlayLevel.NONE.value),
            },
        },
        "narrative_profile": {
            "archetype_summary": f"Avatar {archetype} diseñado para operar con una identidad consistente dentro de la vertical {vertical}.",
            "origin_story": narrative_minimal.get("origin") or "Identidad sintetica creada para sostener una narrativa consistente y comercialmente viable.",
            "motivations": ["grow_premium_audience", "protect_brand_consistency"],
            "interests": interests,
            "audience_role": AudienceRole.ASPIRATIONAL.value if vertical == Vertical.LIFESTYLE.value else AudienceRole.FANTASY_GUIDE.value,
            "conversational_hooks": ["after_hours_stories", "style_breakdowns"],
            "minimal_viable_profile": {
                "origin": narrative_minimal.get("origin", "Identidad sintetica creada para una presencia premium y trazable."),
                "interests": interests,
                "daily_life": narrative_minimal.get("daily_life", "Alterna contenido curado, presencia social y rituales esteticos repetibles."),
                "motivation": narrative_minimal.get("motivation", "Convertir la identidad en una marca consistente y rentable."),
                "relationship_with_fans": narrative_minimal.get(
                    "relationship_with_fans",
                    "Se relaciona con cercania medida y una sensacion de exclusividad sostenida.",
                ),
            },
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
            "persona_summary": f"{display_name} es una identidad sintetica lista para Sistema 1 con sesgo {style} y vertical {vertical}.",
            "greeting_style": "Abre con curiosidad segura y una invitacion breve.",
            "reply_style_keywords": ["flirty", "direct", style],
            "memory_tags": ["style_preferences", "favorite_scenarios"],
            "prohibited_topics": ["illegal_content", "real_world_personal_data"],
            "upsell_style": "Escala desde complicidad ligera hacia premium sin romper personaje.",
        },
        "traceability": {
            "source_issue_id": settings.source_issue_id,
            "source_epic_id": settings.source_epic_id,
            "contract_owner": settings.contract_owner,
            "future_systems_ready": ["system_2", "system_5"],
            "last_reviewed_at": "2026-03-30T15:00:00+00:00",
            "field_traces": field_traces,
        },
    }


def _coerce_expansion_payload(raw_payload: dict, settings: AgenticSettings, idea: str) -> dict:
    payload = dict(raw_payload)
    if not isinstance(payload.get("assumptions"), list):
        payload["assumptions"] = ["real_llm_smoke"]
    completion_report = dict(payload.get("completion_report", {}) or {})
    normalized_constraints = dict(payload.get("normalized_constraints", {}) or {})
    identity_draft = dict(payload.get("identity_draft", {}) or {})
    if "field_traces" not in identity_draft or not identity_draft.get("field_traces"):
        identity_draft["field_traces"] = _build_field_traces(payload, idea)
    if "manually_defined_fields" not in completion_report:
        completion_report["manually_defined_fields"] = normalized_constraints.get("explicitly_defined_fields", [])
    if "inferred_fields" not in completion_report or not completion_report.get("inferred_fields"):
        completion_report["inferred_fields"] = [
            trace["field_path"]
            for trace in identity_draft["field_traces"]
            if trace.get("origin") in {"inferred", "defaulted", "derived"}
        ]
    if "missing_fields" not in completion_report:
        completion_report["missing_fields"] = []
    technical_sheet_payload = payload.get("technical_sheet_payload")
    if not isinstance(technical_sheet_payload, dict) or "identity_core" not in technical_sheet_payload:
        payload["technical_sheet_payload"] = _build_technical_sheet_from_identity(payload, settings, idea)
    payload["identity_draft"] = identity_draft
    payload["completion_report"] = completion_report
    return payload


@dataclass
class OpenAICompatibleLLMClient:
    settings: AgenticSettings

    def generate_expansion(
        self,
        idea: str,
        critique_history: list[CritiqueIssue],
        attempt_count: int,
    ) -> ExpansionResult:
        llm_base_url = self.settings.resolved_llm_base_url
        llm_model = self.settings.resolved_llm_model
        llm_api_key = self.settings.resolved_llm_api_key
        if not llm_base_url:
            raise RuntimeError("LLM_SERVERLESS_BASE_URL or OPENAI_API_KEY is required for the real LLM adapter")
        if not llm_model:
            raise RuntimeError("LLM_SERVERLESS_MODEL or OPENAI_MODEL is required for the real LLM adapter")

        critique_lines = [f"{issue.code}: {issue.message}" for issue in critique_history] or ["none"]
        valid_values = {
            "category": _enum_values(CreationCategory),
            "vertical": _enum_values(Vertical),
            "style": _enum_values(IdentityStyle),
            "archetype": _enum_values(ArchetypeCode),
            "trait_scale": _enum_values(TraitScale),
            "speech_style": _enum_values(SpeechStyle),
            "voice_tone": _enum_values(VoiceTone),
            "message_length": _enum_values(MessageLength),
            "emoji_usage": _enum_values(EmojiUsage),
            "punctuation_style": _enum_values(PunctuationStyle),
            "fan_relationship_style": _enum_values(FanRelationshipStyle),
            "attention_strategy": _enum_values(AttentionStrategy),
            "response_energy": _enum_values(ResponseEnergy),
            "jealousy_play": _enum_values(JealousyPlayLevel),
        }
        instructions = (
            "You are generating a VixenBliss ExpansionResult object. "
            "Return exactly one JSON object with these top-level keys only: "
            "expansion_summary, prompt_blueprint, assumptions, normalized_constraints, identity_draft, completion_report, technical_sheet_payload. "
            "Do not echo the request payload. Do not include idea, attempt_count, critique_history, schema_hint, markdown, explanations, or comments. "
            "Preserve manually defined fields and infer only missing values. "
            "Use only the allowed enum values provided. "
            "technical_sheet_payload must be a complete TechnicalSheet object, not an empty object."
        )
        schema_hint = {
            "normalized_constraints": {
                "category": "CreationCategory",
                "vertical": "Vertical",
                "style": "IdentityStyle",
                "occupation_or_content_basis": "string",
                "archetype": "ArchetypeCode",
                "speech_style": "SpeechStyle",
                "voice_tone": "VoiceTone",
                "explicitly_defined_fields": ["field.path"],
                "source_excerpt": "string",
            },
            "identity_draft": {
                "metadata": {
                    "avatar_id": "string|null",
                    "category": "CreationCategory",
                    "vertical": "Vertical",
                    "style": "IdentityStyle",
                    "occupation_or_content_basis": "string",
                },
                "name": "string",
                "archetype": "ArchetypeCode",
                "personality_axes": {
                    "dominance": "TraitScale",
                    "warmth": "TraitScale",
                    "playfulness": "TraitScale",
                    "mystery": "TraitScale",
                    "flirtiness": "TraitScale",
                    "intelligence": "TraitScale",
                    "sarcasm": "TraitScale",
                },
                "communication_style": {
                    "speech_style": "SpeechStyle",
                    "message_length": "MessageLength",
                    "emoji_usage": "EmojiUsage",
                    "emoji_style": "string|null",
                    "punctuation_style": "PunctuationStyle",
                },
                "social_behavior": {
                    "fan_relationship_style": "FanRelationshipStyle",
                    "attention_strategy": "AttentionStrategy",
                    "response_energy": "ResponseEnergy",
                    "jealousy_play": "JealousyPlayLevel",
                },
                "narrative_minimal": {
                    "origin": "string",
                    "interests": ["string"],
                    "daily_life": "string",
                    "motivation": "string",
                    "relationship_with_fans": "string",
                },
                "field_traces": [
                    {
                        "field_path": "string",
                        "origin": "manual|inferred|defaulted|derived",
                        "source_text": "string|null",
                        "confidence": "number|null",
                        "rationale": "string|null",
                    }
                ],
            },
            "completion_report": {
                "manually_defined_fields": ["field.path"],
                "inferred_fields": ["field.path"],
                "missing_fields": [],
            },
            "technical_sheet_payload": "TechnicalSheet JSON object",
        }
        payload = {
            "model": llm_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": json.dumps(
                        {
                            "instructions": instructions,
                            "valid_values": valid_values,
                            "schema_hint": schema_hint,
                        }
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "idea": idea,
                            "attempt_count": attempt_count,
                            "critique_history": critique_lines,
                        }
                    ),
                },
            ],
        }
        headers = {"Content-Type": "application/json"}
        if llm_api_key:
            headers["Authorization"] = f"Bearer {llm_api_key}"
        url = llm_base_url.rstrip("/") + "/chat/completions"
        response_payload = _json_post(url, payload, headers)
        content = response_payload["choices"][0]["message"]["content"]
        return ExpansionResult.model_validate(_coerce_expansion_payload(json.loads(content), self.settings, idea))


@dataclass
class ComfyUICopilotHTTPClient:
    settings: AgenticSettings

    def recommend_workflow(self, expansion: ExpansionResult) -> CopilotRecommendation:
        if not self.settings.comfyui_copilot_base_url:
            raise RuntimeError("COMFYUI_COPILOT_BASE_URL is required for the real Copilot adapter")

        headers = {"Content-Type": "application/json"}
        if self.settings.comfyui_copilot_api_key:
            headers["Authorization"] = f"Bearer {self.settings.comfyui_copilot_api_key}"
        url = parse.urljoin(
            self.settings.comfyui_copilot_base_url.rstrip("/") + "/",
            self.settings.comfyui_copilot_path.lstrip("/"),
        )
        response_payload = _json_post(
            url,
            {
                "expansion_summary": expansion.expansion_summary,
                "prompt_blueprint": expansion.prompt_blueprint,
                "technical_sheet_payload": expansion.technical_sheet_payload.model_dump(mode="json"),
            },
            headers,
        )
        return CopilotRecommendation.model_validate(response_payload)


@dataclass
class FakeLLMClient:
    sequence: list[ExpansionResult] = field(default_factory=list)
    factory: Callable[[str, list[CritiqueIssue], int], ExpansionResult | dict] | None = None
    _calls: int = field(default=0, init=False, repr=False)

    def generate_expansion(
        self,
        idea: str,
        critique_history: list[CritiqueIssue],
        attempt_count: int,
    ) -> ExpansionResult:
        if self.factory is not None:
            payload = self.factory(idea, critique_history, attempt_count)
            return ExpansionResult.model_validate(payload)
        if self._calls >= len(self.sequence):
            raise RuntimeError("FakeLLMClient sequence exhausted")
        item = self.sequence[self._calls]
        self._calls += 1
        return item


@dataclass
class FakeCopilotClient:
    sequence: list[CopilotRecommendation] = field(default_factory=list)
    factory: Callable[[ExpansionResult], CopilotRecommendation | dict] | None = None
    _calls: int = field(default=0, init=False, repr=False)

    def recommend_workflow(self, expansion: ExpansionResult) -> CopilotRecommendation:
        if self.factory is not None:
            payload = self.factory(expansion)
            return CopilotRecommendation.model_validate(payload)
        if self._calls >= len(self.sequence):
            raise RuntimeError("FakeCopilotClient sequence exhausted")
        item = self.sequence[self._calls]
        self._calls += 1
        return item
