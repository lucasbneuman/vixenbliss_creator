from __future__ import annotations

from vixenbliss_creator.s1_control.avatar_report import build_avatar_report


def test_avatar_report_projects_human_readable_sections() -> None:
    row = {
        "avatar_id": "avatar-1",
        "alias": "luna",
        "display_name": "Luna",
        "status": "draft",
        "pipeline_state": "dataset_ready",
        "dataset_status": "ready",
        "source_prompt_request_id": "47",
        "category": "adult_creator",
        "vertical": "adult_entertainment",
        "style": "glam",
        "occupation_or_content_basis": "modelo rubia ojos claros para contenidos NSFW",
        "allowed_content_modes": ["sfw", "sensual", "nsfw"],
        "base_image_urls": ["https://directus.example.com/assets/base-image"],
        "reference_face_image_url": "https://directus.example.com/assets/base-image",
        "latest_base_model_id": "flux-schnell-v1",
        "latest_workflow_id": "base-image-ipadapter-impact",
        "latest_workflow_version": "2026-04-03",
        "latest_seed_bundle_json": {"portrait_seed": 1, "variation_seed": 2, "dataset_seed": 3},
        "latest_dataset_package_uri": "/app/data/artifacts/avatar-1/dataset-package.zip",
        "latest_generation_manifest_json": {
            "prompt": "Character: Luna. Archetype: girl_next_door.",
            "negative_prompt": "identity drift",
        },
        "latest_visual_config_json": {
            "dataset_storage_mode": "directus_images_and_rows",
            "dataset_validation_status": "apto",
            "dataset_validation_report_uri": "dataset-validation://avatar-1/89",
        },
        "latest_dataset_manifest_json": {"dataset_version": "dataset-123", "sample_count": 24},
        "technical_sheet_json": {
            "identity_metadata": {
                "avatar_id": "avatar-1",
                "category": "adult_creator",
                "vertical": "adult_entertainment",
                "style": "glam",
                "occupation_or_content_basis": "modelo rubia ojos claros para contenidos NSFW",
            },
            "identity_core": {
                "display_name": "Luna",
                "tagline": "Identidad sintetica de estilo glam preparada para Sistema 1.",
            },
            "visual_profile": {
                "archetype": "editorial nocturna",
                "eye_color": "hazel",
                "hair_color": "dark_brown",
            },
            "personality_profile": {
                "archetype": "girl_next_door",
                "voice_tone": "seductive",
                "axes": {"warmth": "high"},
                "communication_style": {"speech_style": "playful"},
                "social_behavior": {"fan_relationship_style": "close_confidant"},
            },
            "narrative_profile": {
                "archetype_summary": "Avatar consistente.",
                "minimal_viable_profile": {"relationship_with_fans": "Cercana."},
            },
            "system5_slots": {
                "persona_summary": "Luna es una identidad sintetica.",
                "reply_style_keywords": ["flirty", "direct", "glam"],
                "conversation_openers": ["What kind of mood are you in tonight?"],
                "relationship_progression": "Moves from warm curiosity to trusted intimacy.",
            },
            "operational_limits": {"allowed_content_modes": ["sfw", "sensual", "nsfw"]},
            "traceability": {
                "source_issue_id": "DEV-31",
                "field_traces": [{"field_path": "style", "origin": "inferred"}],
            },
        },
    }

    report = build_avatar_report(row)

    assert report["identity"]["avatar_id"] == "avatar-1"
    assert report["business_profile"]["style"] == "glam"
    assert report["personality_profile"]["archetype"] == "girl_next_door"
    assert report["system5_slots"]["persona_summary"] == "Luna es una identidad sintetica."
    assert report["system5_slots"]["conversation_openers"] == ["What kind of mood are you in tonight?"]
    assert report["generation"]["prompt"] == "Character: Luna. Archetype: girl_next_door."
    assert report["review_snapshot"]["dataset_storage_mode"] == "directus_images_and_rows"
    assert report["traceability"]["source_issue_id"] == "DEV-31"
