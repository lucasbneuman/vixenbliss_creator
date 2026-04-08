from __future__ import annotations

import argparse
import json
from typing import Any

from .config import S1ControlSettings
from .directus import DirectusControlPlaneClient
from .support import load_local_env


def _enum_or_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _latest_identity_row(client: DirectusControlPlaneClient) -> dict[str, Any] | None:
    rows = client.list_items("s1_identities", params={"sort[]": "-id", "limit": "1"})
    return rows[0] if rows else None


def _resolve_identity_row(
    client: DirectusControlPlaneClient,
    *,
    identity_id: str | None = None,
    latest: bool = False,
) -> dict[str, Any]:
    if latest or not identity_id:
        row = _latest_identity_row(client)
        if row is None:
            raise RuntimeError("No identities found in s1_identities")
        return row

    rows = client.list_items("s1_identities", params={"filter[avatar_id][_eq]": identity_id, "limit": "1"})
    if rows:
        return rows[0]
    raise RuntimeError(f"Identity not found for avatar_id={identity_id}")


def build_avatar_report(row: dict[str, Any]) -> dict[str, Any]:
    technical_sheet = row.get("technical_sheet_json") or {}
    identity_metadata = technical_sheet.get("identity_metadata") or {}
    identity_core = technical_sheet.get("identity_core") or {}
    visual_profile = technical_sheet.get("visual_profile") or {}
    personality_profile = technical_sheet.get("personality_profile") or {}
    communication_style = personality_profile.get("communication_style") or {}
    social_behavior = personality_profile.get("social_behavior") or {}
    narrative_profile = technical_sheet.get("narrative_profile") or {}
    minimal_profile = narrative_profile.get("minimal_viable_profile") or {}
    system5_slots = technical_sheet.get("system5_slots") or {}
    traceability = technical_sheet.get("traceability") or {}
    latest_manifest = row.get("latest_generation_manifest_json") or {}
    latest_visual_config = row.get("latest_visual_config_json") or {}
    latest_dataset_manifest = row.get("latest_dataset_manifest_json") or {}

    return {
        "identity": {
            "avatar_id": row.get("avatar_id"),
            "alias": row.get("alias"),
            "display_name": row.get("display_name") or identity_core.get("display_name"),
            "status": row.get("status"),
            "pipeline_state": row.get("pipeline_state"),
            "dataset_status": row.get("dataset_status"),
            "source_prompt_request_id": row.get("source_prompt_request_id"),
        },
        "business_profile": {
            "category": row.get("category") or identity_metadata.get("category"),
            "vertical": row.get("vertical") or identity_metadata.get("vertical"),
            "style": row.get("style") or identity_metadata.get("style"),
            "occupation_or_content_basis": row.get("occupation_or_content_basis")
            or identity_metadata.get("occupation_or_content_basis"),
            "tagline": identity_core.get("tagline"),
            "allowed_content_modes": row.get("allowed_content_modes") or technical_sheet.get("operational_limits", {}).get("allowed_content_modes"),
        },
        "visual_profile": {
            "archetype": visual_profile.get("archetype"),
            "body_type": visual_profile.get("body_type"),
            "skin_tone": visual_profile.get("skin_tone"),
            "eye_color": visual_profile.get("eye_color"),
            "hair_color": visual_profile.get("hair_color"),
            "hair_style": visual_profile.get("hair_style"),
            "dominant_features": visual_profile.get("dominant_features"),
            "wardrobe_styles": visual_profile.get("wardrobe_styles"),
            "visual_must_haves": visual_profile.get("visual_must_haves"),
            "visual_never_do": visual_profile.get("visual_never_do"),
        },
        "personality_profile": {
            "archetype": personality_profile.get("archetype"),
            "voice_tone": personality_profile.get("voice_tone"),
            "primary_traits": personality_profile.get("primary_traits"),
            "secondary_traits": personality_profile.get("secondary_traits"),
            "interaction_style": personality_profile.get("interaction_style"),
            "axes": personality_profile.get("axes"),
            "communication_style": communication_style,
            "social_behavior": social_behavior,
        },
        "narrative_profile": {
            "archetype_summary": narrative_profile.get("archetype_summary"),
            "origin_story": narrative_profile.get("origin_story"),
            "motivations": narrative_profile.get("motivations"),
            "interests": narrative_profile.get("interests"),
            "audience_role": narrative_profile.get("audience_role"),
            "conversational_hooks": narrative_profile.get("conversational_hooks"),
            "minimal_viable_profile": minimal_profile,
        },
        "system5_slots": {
            "persona_summary": system5_slots.get("persona_summary"),
            "greeting_style": system5_slots.get("greeting_style"),
            "reply_style_keywords": system5_slots.get("reply_style_keywords"),
            "memory_tags": system5_slots.get("memory_tags"),
            "prohibited_topics": system5_slots.get("prohibited_topics"),
            "upsell_style": system5_slots.get("upsell_style"),
            "conversation_openers": system5_slots.get("conversation_openers"),
            "emotional_triggers": system5_slots.get("emotional_triggers"),
            "fantasy_pillars": system5_slots.get("fantasy_pillars"),
            "relationship_progression": system5_slots.get("relationship_progression"),
            "tone_guardrails": system5_slots.get("tone_guardrails"),
        },
        "generation": {
            "base_model_id": row.get("latest_base_model_id") or latest_manifest.get("base_model_id"),
            "workflow_id": row.get("latest_workflow_id") or latest_manifest.get("workflow_id"),
            "workflow_version": row.get("latest_workflow_version") or latest_manifest.get("workflow_version"),
            "prompt": latest_manifest.get("prompt"),
            "negative_prompt": latest_manifest.get("negative_prompt"),
            "seed_bundle": row.get("latest_seed_bundle_json") or latest_manifest.get("seed_bundle"),
        },
        "review_snapshot": {
            "dataset_storage_mode": latest_visual_config.get("dataset_storage_mode"),
            "dataset_validation_status": latest_visual_config.get("dataset_validation_status"),
            "dataset_validation_report_uri": latest_visual_config.get("dataset_validation_report_uri"),
            "base_image_urls": row.get("base_image_urls") or [],
            "reference_face_image_url": row.get("reference_face_image_url"),
            "dataset_version": latest_dataset_manifest.get("dataset_version"),
            "sample_count": latest_dataset_manifest.get("sample_count"),
            "dataset_package_uri": row.get("latest_dataset_package_uri"),
        },
        "traceability": {
            "source_issue_id": traceability.get("source_issue_id"),
            "source_epic_id": traceability.get("source_epic_id"),
            "contract_owner": traceability.get("contract_owner"),
            "last_reviewed_at": traceability.get("last_reviewed_at"),
            "field_traces": traceability.get("field_traces"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Show a human-readable avatar report from s1_identities.")
    parser.add_argument("--identity-id", help="avatar_id to inspect. If omitted, the latest identity is used.")
    parser.add_argument("--latest", action="store_true", help="Force reading the latest identity row.")
    args = parser.parse_args()

    load_local_env()
    client = DirectusControlPlaneClient(S1ControlSettings.from_env())
    row = _resolve_identity_row(client, identity_id=args.identity_id, latest=args.latest)
    report = build_avatar_report(row)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
