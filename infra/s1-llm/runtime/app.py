from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib import error, request

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect

from vixenbliss_creator.contracts.identity import (
    ArchetypeCode,
    AttentionStrategy,
    AudienceRole,
    CreationCategory,
    EmojiUsage,
    FanRelationshipStyle,
    IdentityStyle,
    JealousyPlayLevel,
    MessageLength,
    PunctuationStyle,
    ResponseEnergy,
    SpeechStyle,
    TraitScale,
    Vertical,
    VoiceTone,
)
from vixenbliss_creator.traceability import normalize_trace_source_text
from vixenbliss_creator.s1_control import S1ControlSettings, S1RuntimeDirectusRecorder
from vixenbliss_creator.s1_services import GenerationServiceInput, InMemoryServiceRuntime, build_generation_manifest


ARTIFACT_ROOT = Path(os.getenv("SERVICE_ARTIFACT_ROOT", "/tmp/vixenbliss/s1-llm"))
ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)

LLM_BACKEND = os.getenv("S1_LLM_BACKEND", "openai").strip().lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1:11434")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
OLLAMA_PULL_ON_START = os.getenv("OLLAMA_PULL_ON_START", "0").lower() in {"1", "true", "yes", "on"}
OLLAMA_STARTUP_ENABLED = os.getenv("OLLAMA_STARTUP_ENABLED", "0").lower() in {"1", "true", "yes", "on"}
OPENAI_API_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_API_KEY = os.getenv("OPEN_AI_TOKEN") or os.getenv("OPENAI_API_KEY") or os.getenv("S1_LLM_RUNTIME_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
DEFAULT_PROVIDER_MODEL = OPENAI_API_MODEL if LLM_BACKEND == "openai" else OLLAMA_MODEL
OPENAI_MODEL_ALIAS = os.getenv("S1_LLM_OPENAI_MODEL_ALIAS", DEFAULT_PROVIDER_MODEL)
OPENAI_DEFAULT_TEMPERATURE = float(os.getenv("S1_LLM_DEFAULT_TEMPERATURE", "0"))
_OLLAMA_PROCESS: subprocess.Popen[str] | None = None


def _json_request(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout_seconds: int | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    req = request.Request(
        url=url,
        data=body,
        headers=request_headers,
        method=method,
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds or OLLAMA_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP error calling {url}: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error calling {url}: {exc.reason}") from exc
    return {} if not raw else json.loads(raw)


def _ollama_available() -> bool:
    return subprocess.run(
        ["ollama", "--version"],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0


def _wait_for_ollama_ready(timeout_seconds: int = 90) -> None:
    deadline = time.time() + timeout_seconds
    last_error = "unknown"
    while time.time() < deadline:
        try:
            _json_request("GET", f"{OLLAMA_BASE_URL}/api/tags", timeout_seconds=5)
            return
        except Exception as exc:  # pragma: no cover - exercised by integration runs
            last_error = str(exc)
            time.sleep(1)
    raise RuntimeError(f"Ollama did not become ready before timeout: {last_error}")


def _ensure_ollama_server() -> None:
    global _OLLAMA_PROCESS
    if LLM_BACKEND != "ollama":
        return
    if _OLLAMA_PROCESS is not None:
        return
    if not OLLAMA_STARTUP_ENABLED:
        return
    if not _ollama_available():
        raise RuntimeError("Ollama binary is not installed in the current runtime")
    env = dict(os.environ)
    env["OLLAMA_HOST"] = OLLAMA_HOST
    _OLLAMA_PROCESS = subprocess.Popen(
        ["ollama", "serve"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    _wait_for_ollama_ready()
    if OLLAMA_PULL_ON_START:
        subprocess.run(["ollama", "pull", OLLAMA_MODEL], check=True, env=env)


def _shutdown_ollama_server() -> None:
    global _OLLAMA_PROCESS
    if LLM_BACKEND != "ollama":
        return
    if _OLLAMA_PROCESS is None:
        return
    _OLLAMA_PROCESS.terminate()
    try:
        _OLLAMA_PROCESS.wait(timeout=10)
    except subprocess.TimeoutExpired:  # pragma: no cover - best effort cleanup
        _OLLAMA_PROCESS.kill()
    _OLLAMA_PROCESS = None


def _persist_manifest(result: dict[str, Any]) -> dict[str, Any]:
    artifact_path = result["generation_manifest"]["artifact_path"]
    target = ARTIFACT_ROOT / Path(artifact_path).name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    result["generation_manifest"]["artifact_path"] = str(target.as_posix())
    return result


def _extract_message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "\n".join(part for part in parts if part)
    return str(content or "")


def _ensure_json_keyword_for_openai(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    combined_text = "\n".join(_extract_message_text(message.get("content", "")) for message in messages)
    if "json" in combined_text.lower():
        return messages
    patched_messages = [dict(message) for message in messages]
    if patched_messages and patched_messages[0].get("role") == "system":
        patched_messages[0]["content"] = f"{_extract_message_text(patched_messages[0].get('content', ''))}\nReturn valid JSON."
        return patched_messages
    return [{"role": "system", "content": "Return valid JSON."}, *patched_messages]


def _requests_json_object(payload: dict[str, Any]) -> bool:
    response_format = payload.get("response_format", {}) or {}
    if response_format.get("type") == "json_object":
        return True
    messages = payload.get("messages", []) or []
    return _extract_langgraph_idea({"response_format": response_format, "messages": messages}) is not None


def _loads_json_object(raw_text: str) -> dict[str, Any] | None:
    text = raw_text.strip()
    if not text:
        return None
    candidates = [text]
    if text.startswith("```"):
        fence_parts = text.split("```")
        if len(fence_parts) >= 3:
            candidates.append(fence_parts[1].removeprefix("json").strip())
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _non_empty_string(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _merge_missing_values(current: dict[str, Any] | None, defaults: dict[str, Any]) -> dict[str, Any]:
    merged = dict(current or {})
    for key, value in defaults.items():
        if key not in merged or merged[key] is None or merged[key] == "":
            merged[key] = value
    return merged


def _infer_constraints_from_idea(idea: str) -> dict[str, Any]:
    lowered = idea.lower()
    vertical = "lifestyle" if "lifestyle" in lowered else "adult_entertainment"
    style = "premium" if "premium" in lowered else "editorial"
    category = "lifestyle_premium" if vertical == "lifestyle" else "adult_creator"
    occupation = "luxury lifestyle creator" if vertical == "lifestyle" else "premium digital performer"
    archetype = "luxury_muse" if vertical == "lifestyle" else "playful_tease"
    voice_tone = "authoritative" if vertical == "lifestyle" else "seductive"
    return {
        "category": category,
        "vertical": vertical,
        "style": style,
        "occupation_or_content_basis": occupation,
        "archetype": archetype,
        "speech_style": "refined",
        "voice_tone": voice_tone,
        "source_excerpt": idea[:240],
    }


def _build_field_traces(payload: dict[str, Any], idea: str) -> list[dict[str, Any]]:
    completion_report = payload.get("completion_report", {}) or {}
    normalized_constraints = payload.get("normalized_constraints", {}) or {}
    explicit = normalized_constraints.get("explicitly_defined_fields", []) or completion_report.get("manually_defined_fields", [])
    manual_fields = [field for field in list(dict.fromkeys(explicit)) if field != "field.path"]
    inferred_fields = [field for field in list(dict.fromkeys(completion_report.get("inferred_fields", []))) if field != "field.path"]
    if not inferred_fields:
        inferred_fields = [
            "metadata.category",
            "metadata.occupation_or_content_basis",
            "archetype",
            "communication_style.speech_style",
            "voice_tone",
        ]
    traces: list[dict[str, Any]] = []
    for field_path in manual_fields:
        traces.append(
            {
                "field_path": field_path,
                "origin": "manual",
                "source_text": normalize_trace_source_text(idea),
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
                "source_text": normalize_trace_source_text(idea),
                "confidence": 0.8,
                "rationale": "Campo completado por inferencia para cerrar la identidad.",
            }
        )
    return traces


def _capped_field_list(values: list[str], *, limit: int = 24) -> list[str]:
    return list(dict.fromkeys(values))[:limit]


def _english_persona_summary(*, display_name: str, style: str, vertical: str, archetype: str) -> str:
    return (
        f"{display_name} is a synthetic identity built for System 1 with a {style} tone, "
        f"{vertical} positioning, and a {archetype} conversational archetype."
    )


def _english_tagline(*, style: str) -> str:
    return f"Synthetic {style} identity prepared for System 1 handoff and downstream content systems."


def _english_interaction_style(vertical: str) -> str:
    return f"Maintains a clear, emotionally controlled, and commercially coherent presence for the {vertical} vertical."


def _english_archetype_summary(*, archetype: str, vertical: str) -> str:
    return f"Avatar built around a {archetype} persona with behavior calibrated for the {vertical} vertical."


def _english_origin_story(*, display_name: str, style: str, vertical: str) -> str:
    return (
        f"{display_name} was designed as a synthetic {style} identity with repeatable visual and conversational "
        f"consistency for the {vertical} vertical."
    )


def _english_daily_life(*, style: str) -> str:
    return (
        f"Balances curated content production, aesthetic routines, and audience-facing moments with a {style} cadence."
    )


def _english_motivation(*, vertical: str) -> str:
    return f"Grow a durable audience presence while protecting brand consistency across {vertical} interactions."


def _english_relationship_with_fans() -> str:
    return "Builds closeness with measured intimacy, emotional control, and a steady sense of exclusivity."


def _default_system5_slots(*, display_name: str, style: str, vertical: str, archetype: str) -> dict[str, Any]:
    return {
        "persona_summary": _english_persona_summary(
            display_name=display_name,
            style=style,
            vertical=vertical,
            archetype=archetype,
        ),
        "greeting_style": "Opens with confident curiosity, light invitation, and immediate emotional presence.",
        "reply_style_keywords": ["flirty", "direct", style],
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
    }


def _build_technical_sheet_from_identity(payload: dict[str, Any], idea: str) -> dict[str, Any]:
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
    voice_tone = normalized_constraints.get("voice_tone") or (
        VoiceTone.AUTHORITATIVE.value if vertical == Vertical.LIFESTYLE.value else VoiceTone.SEDUCTIVE.value
    )
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
            "tagline": _english_tagline(style=style),
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
            "interaction_style": _english_interaction_style(vertical),
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
                "fan_relationship_style": social_behavior.get(
                    "fan_relationship_style",
                    FanRelationshipStyle.ASPIRATIONAL_MUSE.value,
                ),
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
            **_default_system5_slots(
                display_name=display_name,
                style=style,
                vertical=vertical,
                archetype=archetype,
            ),
        },
        "traceability": {
            "source_issue_id": os.getenv("AGENTIC_BRAIN_SOURCE_ISSUE_ID", "DEV-7"),
            "source_epic_id": os.getenv("AGENTIC_BRAIN_SOURCE_EPIC_ID", "DEV-3"),
            "contract_owner": os.getenv("AGENTIC_BRAIN_CONTRACT_OWNER", "Codex"),
            "future_systems_ready": ["system_2", "system_5"],
            "last_reviewed_at": "2026-03-30T15:00:00+00:00",
            "field_traces": field_traces,
        },
    }


def _build_langgraph_payload(raw_payload: dict[str, Any], idea: str) -> dict[str, Any]:
    payload = dict(raw_payload)
    payload["expansion_summary"] = _non_empty_string(payload.get("expansion_summary")) or (
        "Expansion inicial lista para construir identidad estructurada, trazable y consumible por Sistema 1."
    )
    payload["prompt_blueprint"] = _non_empty_string(payload.get("prompt_blueprint")) or (
        "Identity blueprint optimized for coherent avatar creation, structured constraints, fixed seeds and safe operational limits."
    )
    assumptions = payload.get("assumptions")
    if not isinstance(assumptions, list) or not assumptions:
        payload["assumptions"] = ["runtime_normalized_from_modal_ollama"]

    normalized_constraints = _merge_missing_values(payload.get("normalized_constraints", {}) or {}, _infer_constraints_from_idea(idea))
    explicitly_defined_fields = normalized_constraints.get("explicitly_defined_fields")
    if not isinstance(explicitly_defined_fields, list):
        normalized_constraints["explicitly_defined_fields"] = []
    payload["normalized_constraints"] = normalized_constraints

    identity_draft = dict(payload.get("identity_draft", {}) or {})
    if "field_traces" not in identity_draft or not identity_draft.get("field_traces"):
        identity_draft["field_traces"] = _build_field_traces(payload, idea)
    payload["identity_draft"] = identity_draft

    technical_sheet = payload.get("technical_sheet_payload")
    if not isinstance(technical_sheet, dict) or "identity_core" not in technical_sheet:
        technical_sheet = _build_technical_sheet_from_identity(payload, idea)
    identity_metadata = technical_sheet.get("identity_metadata", {}) or {}
    personality_profile = technical_sheet.get("personality_profile", {}) or {}
    identity_core = technical_sheet.get("identity_core", {}) or {}
    technical_sheet["identity_core"] = {
        **identity_core,
        "tagline": _english_tagline(style=str(identity_metadata.get("style") or IdentityStyle.EDITORIAL.value)),
    }
    technical_sheet["personality_profile"] = {
        **personality_profile,
        "interaction_style": _english_interaction_style(
            str(identity_metadata.get("vertical") or Vertical.ADULT_ENTERTAINMENT.value)
        ),
    }
    narrative_profile = dict(technical_sheet.get("narrative_profile", {}) or {})
    minimal_profile = dict(narrative_profile.get("minimal_viable_profile", {}) or {})
    display_name = str(identity_core.get("display_name") or "Velvet Ember")
    style = str(identity_metadata.get("style") or IdentityStyle.EDITORIAL.value)
    vertical = str(identity_metadata.get("vertical") or Vertical.ADULT_ENTERTAINMENT.value)
    archetype = str(personality_profile.get("archetype") or ArchetypeCode.PLAYFUL_TEASE.value)
    narrative_profile["archetype_summary"] = _english_archetype_summary(archetype=archetype, vertical=vertical)
    narrative_profile["origin_story"] = _english_origin_story(display_name=display_name, style=style, vertical=vertical)
    minimal_profile["origin"] = _english_origin_story(display_name=display_name, style=style, vertical=vertical)
    minimal_profile["daily_life"] = _english_daily_life(style=style)
    minimal_profile["motivation"] = _english_motivation(vertical=vertical)
    minimal_profile["relationship_with_fans"] = _english_relationship_with_fans()
    narrative_profile["minimal_viable_profile"] = minimal_profile
    technical_sheet["narrative_profile"] = narrative_profile
    system5_slots = dict(technical_sheet.get("system5_slots", {}) or {})
    system5_defaults = _default_system5_slots(
        display_name=display_name,
        style=style,
        vertical=vertical,
        archetype=archetype,
    )
    for key, value in system5_defaults.items():
        if key not in system5_slots or not system5_slots.get(key):
            system5_slots[key] = value
    system5_slots["persona_summary"] = system5_defaults["persona_summary"]
    system5_slots["greeting_style"] = system5_defaults["greeting_style"]
    system5_slots["upsell_style"] = system5_defaults["upsell_style"]
    technical_sheet["system5_slots"] = system5_slots
    payload["technical_sheet_payload"] = technical_sheet
    traceability = technical_sheet.get("traceability", {}) or {}
    field_traces = traceability.get("field_traces", []) or []
    identity_metadata = technical_sheet.get("identity_metadata", {}) or {}
    personality_profile = technical_sheet.get("personality_profile", {}) or {}
    communication_style = personality_profile.get("communication_style", {}) or {}
    social_behavior = personality_profile.get("social_behavior", {}) or {}
    narrative_profile = technical_sheet.get("narrative_profile", {}) or {}
    minimal_profile = narrative_profile.get("minimal_viable_profile", {}) or {}

    identity_draft = dict(payload.get("identity_draft", {}) or {})
    identity_draft["metadata"] = _merge_missing_values(identity_draft.get("metadata", {}) or {}, identity_metadata)
    identity_draft["name"] = _non_empty_string(identity_draft.get("name")) or technical_sheet.get("identity_core", {}).get("display_name", "Velvet Ember")
    identity_draft["archetype"] = _non_empty_string(identity_draft.get("archetype")) or personality_profile.get("archetype", normalized_constraints["archetype"])
    identity_draft["personality_axes"] = _merge_missing_values(identity_draft.get("personality_axes", {}) or {}, personality_profile.get("axes", {}))
    identity_draft["communication_style"] = _merge_missing_values(identity_draft.get("communication_style", {}) or {}, communication_style)
    identity_draft["social_behavior"] = _merge_missing_values(identity_draft.get("social_behavior", {}) or {}, social_behavior)
    identity_draft["narrative_minimal"] = _merge_missing_values(identity_draft.get("narrative_minimal", {}) or {}, minimal_profile)
    identity_draft["field_traces"] = identity_draft.get("field_traces") or field_traces
    payload["identity_draft"] = identity_draft

    manual_fields = [
        trace.get("field_path")
        for trace in field_traces
        if trace.get("origin") == "manual" and trace.get("field_path")
    ]
    inferred_fields = [
        trace.get("field_path")
        for trace in field_traces
        if trace.get("origin") in {"inferred", "defaulted", "derived"} and trace.get("field_path")
    ]
    payload["completion_report"] = {
        "manually_defined_fields": _capped_field_list(manual_fields),
        "inferred_fields": _capped_field_list(inferred_fields),
        "missing_fields": [],
    }
    return payload


def _extract_langgraph_idea(payload: dict[str, Any]) -> str | None:
    if payload.get("response_format", {}).get("type") != "json_object":
        return None
    messages = payload.get("messages", []) or []
    system_text = "\n".join(
        _extract_message_text(message.get("content", ""))
        for message in messages
        if message.get("role") == "system"
    )
    if "ExpansionResult" not in system_text and "VixenBliss" not in system_text:
        return None
    for message in messages:
        if message.get("role") != "user":
            continue
        user_text = _extract_message_text(message.get("content", ""))
        parsed = _loads_json_object(user_text)
        if isinstance(parsed, dict) and parsed.get("idea"):
            return str(parsed["idea"])
        if user_text.strip():
            return user_text.strip()
    return None


def _normalize_chat_response_for_langgraph(request_payload: dict[str, Any], response_payload: dict[str, Any]) -> dict[str, Any]:
    idea = _extract_langgraph_idea(request_payload)
    if not idea:
        return response_payload
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return response_payload
    message = choices[0].get("message", {}) or {}
    content = _extract_message_text(message.get("content", ""))
    parsed = _loads_json_object(content) or {}
    normalized_content = json.dumps(_build_langgraph_payload(parsed, idea), ensure_ascii=False)
    normalized = dict(response_payload)
    normalized_choices = [dict(choice) for choice in choices]
    normalized_message = dict(normalized_choices[0].get("message", {}) or {})
    normalized_message["content"] = normalized_content
    normalized_choices[0]["message"] = normalized_message
    normalized["choices"] = normalized_choices
    return normalized


def _processor(payload: dict[str, Any]) -> dict[str, Any]:
    request_model = GenerationServiceInput.model_validate(payload)
    manifest = build_generation_manifest(request_model)
    return _persist_manifest(
        {
            "service": "s1_llm",
            "provider": "modal",
            "generation_manifest": manifest.model_dump(mode="json"),
        }
    )


def _record_directus_chat_completion(chat_payload: dict[str, Any], response_payload: dict[str, Any]) -> None:
    metadata = chat_payload.get("metadata", {}) or {}
    identity_id = metadata.get("identity_id")
    directus_run_id = metadata.get("directus_run_id")
    prompt_request_id = metadata.get("prompt_request_id")
    if _directus_recorder is None or not any([identity_id, directus_run_id, prompt_request_id]):
        return
    user_prompt = ""
    for message in chat_payload.get("messages", []):
        if message.get("role") == "user":
            user_prompt = str(message.get("content", ""))
            break
    _directus_recorder.record_job(
        service_name="s1_llm_completion",
        job_id=response_payload.get("id", f"chatcmpl-{uuid.uuid4().hex[:12]}"),
        status="completed",
        input_payload={
            "identity_id": identity_id,
            "directus_run_id": directus_run_id,
            "prompt_request_id": prompt_request_id,
            "prompt": user_prompt,
        },
        result_payload={
            "provider": "modal",
            "model": response_payload.get("model", OPENAI_MODEL_ALIAS),
            "llm_backend": LLM_BACKEND,
            "artifacts": [],
            "completion": response_payload,
        },
    )


def _provider_ready_status() -> tuple[bool, dict[str, Any]]:
    if LLM_BACKEND == "openai":
        if not OPENAI_API_KEY:
            return False, {"openai_configured": False}
        try:
            _json_request(
                "GET",
                f"{OPENAI_API_BASE_URL}/models",
                timeout_seconds=10,
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            )
            return True, {"openai_configured": True}
        except Exception as exc:
            return False, {"openai_configured": True, "provider_error": str(exc)}
    ollama_ready = False
    try:
        _json_request("GET", f"{OLLAMA_BASE_URL}/api/tags", timeout_seconds=5)
        ollama_ready = True
    except Exception as exc:
        return False, {"ollama_ready": False, "provider_error": str(exc)}
    return ollama_ready, {"ollama_ready": ollama_ready}


def _chat_completion_payload(payload: dict[str, Any]) -> dict[str, Any]:
    original_payload = dict(payload)
    proxied_payload = dict(payload)
    proxied_payload.pop("metadata", None)
    proxied_payload.setdefault("model", DEFAULT_PROVIDER_MODEL)
    proxied_payload.setdefault("temperature", OPENAI_DEFAULT_TEMPERATURE)
    if LLM_BACKEND == "openai":
        if not OPENAI_API_KEY:
            raise RuntimeError("OPEN_AI_TOKEN or OPENAI_API_KEY is required when S1_LLM_BACKEND=openai")
        messages = proxied_payload.get("messages")
        if isinstance(messages, list) and _requests_json_object(proxied_payload):
            proxied_payload["messages"] = _ensure_json_keyword_for_openai(messages)
        response_payload = _json_request(
            "POST",
            f"{OPENAI_API_BASE_URL}/chat/completions",
            payload=proxied_payload,
            timeout_seconds=OLLAMA_TIMEOUT_SECONDS,
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        )
    else:
        response_payload = _json_request(
            "POST",
            f"{OLLAMA_BASE_URL}/v1/chat/completions",
            payload=proxied_payload,
            timeout_seconds=OLLAMA_TIMEOUT_SECONDS,
        )
    response_payload = _normalize_chat_response_for_langgraph(proxied_payload, response_payload)
    if "model" in response_payload:
        response_payload["model"] = OPENAI_MODEL_ALIAS
    _record_directus_chat_completion(original_payload, response_payload)
    return response_payload


def _list_models_payload() -> dict[str, Any]:
    if LLM_BACKEND == "openai":
        return {
            "object": "list",
            "data": [
                {
                    "id": OPENAI_MODEL_ALIAS,
                    "object": "model",
                    "created": 0,
                    "owned_by": "openai",
                }
            ],
        }
    tags = _json_request("GET", f"{OLLAMA_BASE_URL}/api/tags", timeout_seconds=10)
    models = []
    for row in tags.get("models", []):
        name = row.get("name", OPENAI_MODEL_ALIAS)
        models.append(
            {
                "id": OPENAI_MODEL_ALIAS if name == OLLAMA_MODEL else name,
                "object": "model",
                "created": 0,
                "owned_by": "modal-ollama",
            }
        )
    if not models:
        models.append({"id": OPENAI_MODEL_ALIAS, "object": "model", "created": 0, "owned_by": "modal-ollama"})
    return {"object": "list", "data": models}


runtime = InMemoryServiceRuntime(processor=_processor)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if LLM_BACKEND == "ollama":
        _ensure_ollama_server()
    yield
    if LLM_BACKEND == "ollama":
        _shutdown_ollama_server()


web_app = FastAPI(title="VixenBliss S1 LLM Runtime", version="1.1.0", lifespan=lifespan)
app = web_app

try:
    _directus_recorder = S1RuntimeDirectusRecorder.from_settings(S1ControlSettings.from_env())
except Exception:
    _directus_recorder = None


@web_app.get("/healthcheck")
def healthcheck() -> dict[str, Any]:
    provider_ready, provider_details = _provider_ready_status()
    return {
        "ok": True,
        "service": "s1_llm",
        "provider": "modal",
        "progress_transport": "websocket_optional",
        "llm_backend": LLM_BACKEND,
        "provider_ready": provider_ready,
        **provider_details,
        "ollama_model": OLLAMA_MODEL,
        "openai_api_model": OPENAI_API_MODEL,
        "openai_model_alias": OPENAI_MODEL_ALIAS,
    }


@web_app.post("/jobs")
def submit_job(payload: dict[str, Any]) -> dict[str, Any]:
    job_input = payload.get("input", payload)
    record = runtime.submit(job_input)
    if _directus_recorder is not None:
        try:
            _directus_recorder.record_job(
                service_name="s1_llm",
                job_id=record.job_id,
                status=record.status.value,
                input_payload=job_input,
                result_payload=record.result,
                error_message=record.error_message,
            )
        except Exception:
            pass
    return record.status_payload(
        progress_url=f"/ws/jobs/{record.job_id}",
        result_url=f"/jobs/{record.job_id}/result",
    )


@web_app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    try:
        record = runtime.status(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    return record.status_payload(
        progress_url=f"/ws/jobs/{record.job_id}",
        result_url=f"/jobs/{record.job_id}/result",
    )


@web_app.get("/jobs/{job_id}/result")
def get_result(job_id: str) -> dict[str, Any]:
    try:
        return runtime.result(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@web_app.post("/chat/completions")
@web_app.post("/v1/chat/completions")
async def chat_completions(payload: dict[str, Any], _: Request) -> dict[str, Any]:
    try:
        return _chat_completion_payload(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@web_app.get("/models")
@web_app.get("/v1/models")
def list_models() -> dict[str, Any]:
    try:
        return _list_models_payload()
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@web_app.websocket("/ws/jobs/{job_id}")
async def stream_job(job_id: str, websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        record = runtime.status(job_id)
    except KeyError:
        await websocket.send_json({"error": "job not found"})
        await websocket.close(code=4404)
        return
    try:
        for event in record.progress_events:
            await websocket.send_json(event.model_dump(mode="json"))
    except WebSocketDisconnect:
        return
    await websocket.close()
