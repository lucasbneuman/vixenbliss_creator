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
    assert manifest.seed_bundle.portrait_seed >= 0
    assert manifest.comfy_parameters["ip_adapter"]["enabled"] is True


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
            samples_target=16,
            metadata_json={"character_id": str(manifest.identity_id)},
        )
    )

    assert result["dataset_manifest"]["sample_count"] == 16
    assert result["dataset_manifest"]["generated_samples"] == 16
    assert result["dataset_manifest"]["character_id"] == str(manifest.identity_id)
    assert result["dataset_manifest"]["dataset_version"].startswith("dataset-")
    assert result["dataset_manifest"]["composition"] == {
        "policy": "balanced_50_50",
        "with_clothes": 8,
        "without_clothes": 8,
    }
    assert len(result["dataset_manifest"]["files"]) == 16
    assert result["dataset_manifest"]["files"][0]["class_name"] == "with_clothes"
    assert result["dataset_manifest"]["files"][-1]["class_name"] == "without_clothes"
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

    with pytest.raises(ValueError, match="samples_target must be even"):
        build_dataset_result(
            DatasetServiceInput(
                identity_id=manifest.identity_id,
                generation_manifest=manifest,
                reference_face_image_url="https://example.com/ref.png",
                samples_target=15,
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
