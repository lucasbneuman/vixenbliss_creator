from __future__ import annotations

from uuid import uuid4

import pytest

from vixenbliss_creator.runtime_providers import JobStatus, ModalRuntimeProviderClient, RuntimeProviderSettings, ServiceRuntime
from vixenbliss_creator.s1_services import (
    DatasetServiceInput,
    GenerationManifest,
    GenerationServiceInput,
    InMemoryServiceRuntime,
    LoraTrainingServiceInput,
    build_dataset_shot_plan,
    build_dataset_result,
    build_generation_manifest,
    build_lora_training_result,
)


def test_generation_manifest_contains_prompt_and_stable_seed_bundle() -> None:
    identity_id = uuid4()
    payload = GenerationServiceInput(
        identity_id=identity_id,
        identity_context={"identity_summary": "Velvet Ember", "voice_tone": "seductive"},
        workflow_id="s1-identity-v1",
        workflow_version="2026-04-02",
        base_model_id="flux-schnell-v1",
    )

    manifest = build_generation_manifest(payload)

    assert manifest.identity_id == identity_id
    assert "Velvet Ember" in manifest.prompt
    assert "Tone: seductive." in manifest.prompt
    assert manifest.seed_bundle.portrait_seed >= 0
    assert manifest.comfy_parameters["ip_adapter"]["enabled"] is True
    assert "identity drift" in manifest.negative_prompt
    assert manifest.samples_target == 40
    assert manifest.realism_profile == "photorealistic_adult_reference_v1"
    assert len(manifest.dataset_shot_plan) == 40
    assert manifest.workflow_family == "flux_identity_reference"
    assert manifest.workflow_registry_source == "approved_internal"


def test_generation_manifest_preserves_personality_context_before_training() -> None:
    identity_id = uuid4()
    identity_context = {
        "identity_summary": "Secure, elegant, and provocative persona with memory for preferences.",
        "summary": "Premium performer with strong visual consistency and safe tone control.",
        "voice_tone": "authoritative",
        "style": "premium",
        "vertical": "lifestyle",
        "occupation_or_content_basis": "coastal adult creator",
        "display_name": "Velvet Ember",
        "archetype": "luxury_muse",
        "personality_axes": {
            "dominance": "medium",
            "warmth": "high",
            "playfulness": "medium",
            "mystery": "high",
            "flirtiness": "high",
            "intelligence": "high",
            "sarcasm": "medium",
        },
        "visual_profile": {
            "hair_color": "red",
            "hair_style": "soft waves",
            "archetype": "coastal editorial portrait",
        },
        "interests": ["animales marinos", "andar en bici", "vida costera"],
    }

    first_manifest = build_generation_manifest(
        GenerationServiceInput(
            identity_id=identity_id,
            identity_context=identity_context,
            workflow_id="s1-identity-v1",
            workflow_version="2026-04-02",
            base_model_id="flux-schnell-v1",
        )
    )
    second_manifest = build_generation_manifest(
        GenerationServiceInput(
            identity_id=identity_id,
            identity_context=identity_context,
            workflow_id="s1-identity-v1",
            workflow_version="2026-04-02",
            base_model_id="flux-schnell-v1",
        )
    )

    assert "Character: Velvet Ember." in first_manifest.prompt
    assert "Archetype: luxury_muse." in first_manifest.prompt
    assert "Commercial profile: lifestyle / premium." in first_manifest.prompt
    assert "Voice tone: authoritative." in first_manifest.prompt
    assert (
        "Create a consistent identity dataset portrait for Velvet Ember, a premium synthetic identity designed for the lifestyle vertical with a luxury_muse archetype."
        in first_manifest.prompt
    )
    assert (
        "Persona summary: Velvet Ember maintains a authoritative delivery with a luxury_muse persona optimized for consistent content generation."
        in first_manifest.prompt
    )
    assert "Identity summary: Synthetic premium identity prepared for repeatable lifestyle content production." in first_manifest.prompt
    assert "Personality axes:" in first_manifest.prompt
    assert "dominance=medium" in first_manifest.prompt
    assert "warmth=high" in first_manifest.prompt
    assert "sarcasm=medium" in first_manifest.prompt
    assert "Content basis: coastal adult creator." in first_manifest.prompt
    assert "Visual cues: red, soft waves, coastal editorial portrait." in first_manifest.prompt
    assert "Interests: animales marinos, andar en bici, vida costera." in first_manifest.prompt
    assert "Figura segura" not in first_manifest.prompt
    assert "consistencia visual" not in first_manifest.prompt
    assert first_manifest.seed_bundle == second_manifest.seed_bundle


def test_generation_manifest_merges_copilot_strategy_into_prompt_and_workflow_metadata() -> None:
    manifest = build_generation_manifest(
        GenerationServiceInput(
            identity_id=uuid4(),
            identity_context={"identity_summary": "Velvet Ember", "style": "editorial", "voice_tone": "seductive"},
            workflow_id="lora-dataset-ipadapter-batch",
            workflow_version="2026-04-08",
            workflow_family="flux_lora_dataset_reference",
            workflow_registry_source="demo_runner",
            base_model_id="flux-schnell-v1",
            copilot_prompt_template="Photorealistic adult dataset workflow with deterministic angle coverage.",
            copilot_negative_prompt="cgi, 3d, illustration, mannequin",
            prompt_hints={"coverage": "full body emphasis", "angles": ["front", "left profile"]},
            negative_prompt_hints={"identity": "identity drift", "artifacts": ["watermark", "text"]},
        )
    )

    assert "Workflow guidance: Photorealistic adult dataset workflow with deterministic angle coverage." in manifest.prompt
    assert "Additional prompt hints: full body emphasis; front; left profile." in manifest.prompt
    assert "cgi" in manifest.negative_prompt
    assert "watermark" in manifest.negative_prompt
    assert manifest.workflow_family == "flux_lora_dataset_reference"
    assert manifest.workflow_registry_source == "demo_runner"
    assert manifest.comfy_parameters["copilot_prompt_template"].startswith("Photorealistic adult dataset workflow")
    assert manifest.comfy_parameters["workflow_family"] == "flux_lora_dataset_reference"


def test_dataset_shot_plan_respects_40_image_coverage_and_prompt_layers() -> None:
    shot_plan = build_dataset_shot_plan(
        dataset_version="dataset-abc123def456",
        avatar_identity_block="avatar identity block with facial and body traits",
        base_negative_prompt="low quality, identity drift",
        seed_bundle={"portrait_seed": 1, "variation_seed": 2, "dataset_seed": 3},
    )

    assert len(shot_plan) == 40
    assert sum(1 for shot in shot_plan if shot.wardrobe_state == "clothed") == 20
    assert sum(1 for shot in shot_plan if shot.wardrobe_state == "nude") == 20
    assert sum(1 for shot in shot_plan if shot.framing == "close_up_face") == 10
    assert sum(1 for shot in shot_plan if shot.framing == "medium") == 10
    assert sum(1 for shot in shot_plan if shot.framing == "full_body") == 20
    assert sum(1 for shot in shot_plan if shot.camera_angle == "front") == 8
    assert "avatar identity block" in shot_plan[0].prompt
    assert "adult real person" in shot_plan[0].prompt
    assert "cgi" in shot_plan[0].negative_prompt
    assert "photorealistic reference photo" in shot_plan[0].caption


def test_dataset_generation_requires_reference_face_when_ip_adapter_enabled() -> None:
    manifest = GenerationManifest.model_validate(
        build_generation_manifest(
            GenerationServiceInput(
                identity_id=uuid4(),
                identity_context={"identity_summary": "Operator-ready profile"},
                workflow_id="s1-identity-v1",
                workflow_version="2026-04-02",
                base_model_id="flux-schnell-v1",
            )
        ).model_dump(mode="json")
    )

    with pytest.raises(ValueError, match="reference_face_image_url"):
        DatasetServiceInput(
            identity_id=manifest.identity_id,
            generation_manifest=manifest,
            reference_face_image_url=None,
        )


def test_dataset_generation_returns_manifest_and_package() -> None:
    manifest = build_generation_manifest(
        GenerationServiceInput(
            identity_id=uuid4(),
            identity_context={"identity_summary": "Operator-ready profile"},
            workflow_id="s1-identity-v1",
            workflow_version="2026-04-02",
            base_model_id="flux-schnell-v1",
            reference_face_image_url="https://example.com/ref.png",
        )
    )

    result = build_dataset_result(
        DatasetServiceInput(
            identity_id=manifest.identity_id,
            generation_manifest=manifest,
            reference_face_image_url="https://example.com/ref.png",
            samples_target=40,
            dataset_shot_plan=manifest.dataset_shot_plan,
            metadata_json={"character_id": str(manifest.identity_id)},
        )
    )

    assert result["dataset_manifest"]["sample_count"] == 40
    assert result["dataset_manifest"]["generated_samples"] == 40
    assert result["dataset_manifest"]["schema_version"] == "1.1.0"
    assert result["dataset_manifest"]["character_id"] == str(manifest.identity_id)
    assert result["dataset_manifest"]["dataset_version"].startswith("dataset-")
    assert result["dataset_manifest"]["storage_path"].endswith(f"/datasets/{result['dataset_manifest']['dataset_version']}")
    assert result["dataset_manifest"]["workflow_extensions"] == ["ComfyUI-BatchingNodes", "ComfyPack"]
    assert result["dataset_manifest"]["workflow_family"] == "flux_identity_reference"
    assert result["dataset_manifest"]["workflow_registry_source"] == "approved_internal"
    assert result["dataset_manifest"]["composition"] == {
        "policy": "balanced_50_50",
        "SFW": 20,
        "NSFW": 20,
    }
    assert len(result["dataset_manifest"]["files"]) == 40
    assert result["dataset_manifest"]["files"][0]["class_name"] == "SFW"
    assert result["dataset_manifest"]["files"][0]["variation_group"] == "close_up_face"
    assert result["dataset_manifest"]["files"][0]["prompt"].startswith("Create a consistent identity dataset portrait")
    assert result["dataset_manifest"]["files"][0]["caption"].endswith("photorealistic reference photo")
    assert result["dataset_manifest"]["files"][0]["camera_angle"] == "front"
    assert result["dataset_manifest"]["files"][0]["realism_profile"] == "photorealistic_adult_reference_v1"
    assert result["dataset_manifest"]["files"][-1]["class_name"] == "NSFW"
    artifact_types = {artifact["artifact_type"] for artifact in result["artifacts"]}
    assert {"base_image", "dataset_manifest", "dataset_package"} <= artifact_types
    base_image_artifact = next(item for item in result["artifacts"] if item["artifact_type"] == "base_image")
    assert base_image_artifact["metadata_json"]["character_id"] == str(manifest.identity_id)
    assert base_image_artifact["metadata_json"]["seed_bundle"]["portrait_seed"] == manifest.seed_bundle.portrait_seed


def test_dataset_generation_requires_even_samples_for_balanced_policy() -> None:
    manifest = build_generation_manifest(
        GenerationServiceInput(
            identity_id=uuid4(),
            identity_context={"identity_summary": "Operator-ready profile"},
            workflow_id="s1-identity-v1",
            workflow_version="2026-04-02",
            base_model_id="flux-schnell-v1",
            reference_face_image_url="https://example.com/ref.png",
        )
    )

    with pytest.raises(ValueError, match="samples_target"):
        build_dataset_result(
            DatasetServiceInput(
                identity_id=manifest.identity_id,
                generation_manifest=manifest,
                reference_face_image_url="https://example.com/ref.png",
                samples_target=19,
                dataset_shot_plan=manifest.dataset_shot_plan[:19],
                metadata_json={"character_id": str(manifest.identity_id)},
            )
        )


def test_lora_training_requires_dataset_source() -> None:
    with pytest.raises(ValueError, match="dataset_manifest or dataset_package_path"):
        LoraTrainingServiceInput(identity_id=uuid4(), base_model_id="flux-schnell-v1")


def test_lora_training_returns_lora_artifact_and_manifest() -> None:
    identity_id = uuid4()
    result = build_lora_training_result(
        LoraTrainingServiceInput(
            identity_id=identity_id,
            dataset_package_path=f"artifacts/{identity_id}/dataset.zip",
            base_model_id="flux-schnell-v1",
            training_config={"training_steps": 1500, "trigger_word": "velvet_ember"},
        )
    )

    assert result["training_manifest"]["training_steps"] == 1500
    assert result["training_manifest"]["dataset_source"]["handoff_mode"] == "dataset_package_path"
    assert result["training_manifest"]["model_registry"]["compatibility_notes"] == "Flux.1 Schnell compliant"
    assert result["artifacts"][0]["artifact_type"] == "lora_model"
    assert result["artifacts"][0]["checksum_sha256"]


def test_in_memory_runtime_records_progress_and_completion() -> None:
    runtime = InMemoryServiceRuntime(processor=lambda payload: {"ok": True, "payload": payload})

    record = runtime.submit({"hello": "world"})

    assert record.status == JobStatus.COMPLETED
    assert len(record.progress_events) == 3
    assert runtime.result(record.job_id)["ok"] is True


def test_modal_runtime_provider_exposes_progress_stream_url(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = RuntimeProviderSettings(
        modal_endpoint_s1_llm="https://modal.example.com/s1-llm",
        modal_token_id="id",
        modal_token_secret="secret",
    )

    def fake_post(url: str, payload: dict, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        assert url == "https://modal.example.com/s1-llm/jobs"
        return {
            "job_id": "modal-job-1",
            "status": "queued",
            "progress_url": "wss://modal.example.com/s1-llm/ws/jobs/modal-job-1",
        }

    monkeypatch.setattr("vixenbliss_creator.runtime_providers.adapters._json_post", fake_post)

    client = ModalRuntimeProviderClient(settings)
    handle = client.submit_job(ServiceRuntime.S1_LLM, {"identity_context": {"summary": "ok"}})

    assert client.progress_stream_url(handle) == "wss://modal.example.com/s1-llm/ws/jobs/modal-job-1"
