from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any
import zipfile

from vixenbliss_creator.s1_control import S1RuntimeDirectusRecorder
from vixenbliss_creator.s1_control.support import tiny_png_bytes


class FakeControlPlane:
    def __init__(self) -> None:
        self.store: dict[str, list[dict[str, Any]]] = {}
        self.sequence = 1
        self.files: list[dict[str, Any]] = []

    def create_item(self, collection: str, payload: dict[str, Any]) -> dict[str, Any]:
        item = {"id": self.sequence, **payload}
        self.sequence += 1
        self.store.setdefault(collection, []).append(item)
        return item

    def update_item(self, collection: str, item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        for item in self.store.get(collection, []):
            if str(item["id"]) == str(item_id):
                item.update(payload)
                return item
        raise KeyError(item_id)

    def read_item(self, collection: str, item_id: str) -> dict[str, Any]:
        for item in self.store.get(collection, []):
            if str(item["id"]) == str(item_id):
                return item
        raise KeyError(item_id)

    def list_items(self, collection: str, *, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        items = list(self.store.get(collection, []))
        if not params:
            return items
        avatar_eq = params.get("filter[avatar_id][_eq]")
        if avatar_eq is not None:
            items = [item for item in items if str(item.get("avatar_id")) == str(avatar_eq)]
        limit = params.get("limit")
        if limit is not None:
            items = items[: int(limit)]
        return items

    def upload_file(
        self,
        file_path: str | Path,
        *,
        storage: str | None = None,
        file_name: str | None = None,
        content_type: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        path = Path(file_path)
        payload = {
            "id": f"file-{self.sequence}",
            "storage": storage or "directus",
            "filename_download": file_name or path.name,
            "type": content_type or "application/octet-stream",
            "filesize": path.stat().st_size,
            "asset_url": f"https://directus.example.com/assets/file-{self.sequence}",
            "title": title,
        }
        self.sequence += 1
        self.files.append(payload)
        return payload


def _build_dataset_manifest(identity_id: str, *, package_path: Path, sample_count: int = 12) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    variation_cycle = ("close_up", "medium", "full_body")
    pose_cycle = ("front", "three_quarter", "profile")
    half = sample_count // 2
    sample_index = 0
    for class_name, count in (("SFW", half), ("NSFW", half)):
        for class_offset in range(count):
            sample_index += 1
            variation_group = variation_cycle[(sample_index - 1) % len(variation_cycle)]
            files.append(
                {
                    "sample_id": f"dataset-{identity_id}-{sample_index:03d}",
                    "identity_id": identity_id,
                    "character_id": identity_id,
                    "class_name": class_name,
                    "variation_group": variation_group,
                    "framing": variation_group,
                    "pose": pose_cycle[(sample_index - 1) % len(pose_cycle)],
                    "path": f"images/{class_name}/sample-{class_offset + 1:03d}.png",
                    "seed": sample_index * 111,
                }
            )
    return {
        "schema_version": "1.0.0",
        "identity_id": identity_id,
        "character_id": identity_id,
        "dataset_version": f"dataset-{identity_id}",
        "dataset_package_path": str(package_path),
        "sample_count": sample_count,
        "generated_samples": sample_count,
        "composition": {"policy": "balanced_50_50", "SFW": half, "NSFW": half},
        "files": files,
        "workflow_id": "base-image-ipadapter-impact",
        "workflow_version": "2026-04-02",
        "base_model_id": "flux-schnell-v1",
        "prompt": "test prompt",
        "negative_prompt": "bad anatomy",
        "seed_bundle": {"portrait_seed": 11, "variation_seed": 22, "dataset_seed": 33},
    }


def _write_dataset_package(package_path: Path, manifest: dict[str, Any]) -> None:
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("dataset-manifest.json", json.dumps(manifest))
        for file_entry in manifest["files"]:
            archive.writestr(file_entry["path"], tiny_png_bytes())


def test_recorder_persists_run_event_and_artifacts(tmp_path: Path) -> None:
    fake = FakeControlPlane()
    identity = fake.create_item("s1_identities", {"avatar_id": "42", "status": "draft"})
    base_path = tmp_path / "base.png"
    base_path.write_bytes(tiny_png_bytes())
    package_path = tmp_path / "dataset.zip"
    manifest = _build_dataset_manifest("42", package_path=package_path)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    _write_dataset_package(package_path, manifest)
    recorder = S1RuntimeDirectusRecorder(client=fake)

    recorder.record_job(
        service_name="s1_image",
        job_id="job-123",
        status="completed",
        input_payload={"identity_id": "42", "prompt": "test prompt"},
        result_payload={
            "provider": "modal",
            "base_model_id": "flux-schnell-v1",
            "workflow_id": "base-image-ipadapter-impact",
            "workflow_version": "2026-04-02",
            "face_detection_confidence": 0.91,
            "dataset_manifest": manifest,
            "metadata": {
                "seed_bundle": {"portrait_seed": 11, "variation_seed": 22, "dataset_seed": 33},
                "prompt": "test prompt",
                "negative_prompt": "bad anatomy",
                "width": 1024,
                "height": 1024,
                "ip_adapter": {"enabled": True},
                "face_detailer": {"enabled": True},
                "reference_face_image_url": "https://example.com/ref.png",
            },
            "artifacts": [
                {
                    "artifact_type": "base_image",
                    "storage_path": str(base_path),
                    "content_type": "image/png",
                    "metadata_json": {"sample_count": 1},
                },
                {
                    "artifact_type": "dataset_manifest",
                    "storage_path": str(manifest_path),
                    "content_type": "application/json",
                    "metadata_json": {"sample_count": 12},
                },
                {
                    "artifact_type": "dataset_package",
                    "storage_path": str(package_path),
                    "content_type": "application/zip",
                    "checksum_sha256": "abc123",
                    "metadata_json": {"sample_count": 12},
                },
            ],
        },
    )

    assert fake.store["s1_generation_runs"][0]["external_job_id"] == "job-123"
    assert any(event["event_type"] == "runtime_job_recorded" for event in fake.store["s1_events"])
    manifest_artifact = next(item for item in fake.store["s1_artifacts"] if item["role"] == "dataset_manifest")
    assert manifest_artifact["file"] is None
    assert manifest_artifact["metadata_json"]["original_storage_path"] == str(manifest_path)
    assert manifest_artifact["metadata_json"]["persistence_target"] == "directus_row"
    package_artifact = next(item for item in fake.store["s1_artifacts"] if item["role"] == "dataset_package")
    assert package_artifact["metadata_json"]["checksum_sha256"] == "abc123"
    assert package_artifact["file"] is None
    validation_artifact = next(item for item in fake.store["s1_artifacts"] if item["role"] == "dataset_validation_report")
    assert validation_artifact["metadata_json"]["validation_status"] == "apto"
    assert len(fake.files) == 1
    assert identity["pipeline_state"] == "dataset_ready"
    assert identity["dataset_status"] == "ready"
    assert identity["dataset_storage_path"] == str(package_path)
    assert identity["base_image_urls"][0].startswith("https://directus.example.com/assets/file-")
    assert identity["reference_face_image_url"].startswith("https://directus.example.com/assets/file-")
    assert identity["reference_face_image_id"].startswith("file-")
    assert identity["base_model_id"] == "flux-schnell-v1"
    assert identity["latest_seed_bundle_json"]["portrait_seed"] == 11
    assert identity["latest_visual_config_json"]["dataset_storage_mode"] == "directus_images_and_rows"
    assert len(identity["latest_visual_config_json"]["persisted_artifacts"]) == 3
    assert identity["latest_base_image_file_id"].startswith("file-")
    assert identity["latest_dataset_manifest_json"]["identity_id"] == "42"
    assert identity["latest_dataset_manifest_file_id"] is None
    assert identity["latest_dataset_package_file_id"] is None
    assert identity["latest_dataset_package_uri"] == str(package_path)
    assert identity["latest_visual_config_json"]["reference_face_image_url"] == "https://example.com/ref.png"
    assert identity["latest_visual_config_json"]["dataset_validation_status"] == "apto"
    base_artifact = next(item for item in fake.store["s1_artifacts"] if item["role"] == "base_image")
    assert base_artifact["metadata_json"]["registration_status"] == "registered"
    assert base_artifact["metadata_json"]["source_job_id"] == "job-123"
    assert any(event["event_type"] == "dataset_validation_passed" for event in fake.store["s1_events"])


def test_recorder_persists_model_asset_for_training_results() -> None:
    fake = FakeControlPlane()
    recorder = S1RuntimeDirectusRecorder(client=fake)

    recorder.record_job(
        service_name="s1_lora_train",
        job_id="job-456",
        status="completed",
        input_payload={"identity_id": "77"},
        result_payload={
            "provider": "modal",
            "artifacts": [],
            "training_manifest": {
                "trigger_word": "vb_77",
                "lora_model_path": "artifacts/s1-lora-train/77/model.safetensors",
                "model_registry": {"version_name": "lora-abc123"},
            },
        },
    )

    assert fake.store["s1_model_assets"][0]["asset_type"] == "lora_model"
    assert fake.store["s1_model_assets"][0]["storage_path"].endswith("model.safetensors")


def test_recorder_updates_existing_run_when_directus_run_id_is_present() -> None:
    fake = FakeControlPlane()
    existing = fake.create_item("s1_generation_runs", {"status": "queued", "identity_id": "55"})
    recorder = S1RuntimeDirectusRecorder(client=fake)

    recorder.record_job(
        service_name="s1_llm",
        job_id="job-789",
        status="completed",
        input_payload={"identity_id": "55", "directus_run_id": existing["id"], "prompt_request_id": "101"},
        result_payload={"provider": "modal", "artifacts": []},
    )

    assert len(fake.store["s1_generation_runs"]) == 1
    assert fake.store["s1_generation_runs"][0]["external_job_id"] == "job-789"
    assert fake.store["s1_generation_runs"][0]["prompt_request_id"] == "101"


def test_recorder_falls_back_when_upload_fails(tmp_path: Path) -> None:
    class FailingControlPlane(FakeControlPlane):
        def upload_file(self, *args, **kwargs) -> dict[str, Any]:
            raise RuntimeError("storage unavailable")

    fake = FailingControlPlane()
    fake.create_item("s1_identities", {"avatar_id": "42", "status": "draft"})
    artifact_path = tmp_path / "manifest.json"
    artifact_path.write_text("{}", encoding="utf-8")
    recorder = S1RuntimeDirectusRecorder(client=fake)

    recorder.record_job(
        service_name="s1_image",
        job_id="job-999",
        status="completed",
        input_payload={"identity_id": "42", "prompt": "test prompt"},
        result_payload={
            "provider": "modal",
            "workflow_version": "2026-04-02",
            "metadata": {},
            "artifacts": [
                {
                    "artifact_type": "dataset_manifest",
                    "storage_path": str(artifact_path),
                    "content_type": "application/json",
                    "metadata_json": {},
                }
            ],
        },
    )

    assert fake.store["s1_artifacts"][0]["file"] is None
    assert fake.store["s1_artifacts"][0]["uri"] == str(artifact_path)
    assert all(event["event_type"] != "runtime_artifact_upload_failed" for event in fake.store["s1_events"])
    assert any(event["event_type"] == "dataset_validation_failed" for event in fake.store["s1_events"])


def test_recorder_publishes_persisted_artifacts_metadata(tmp_path: Path) -> None:
    fake = FakeControlPlane()
    fake.create_item("s1_identities", {"avatar_id": "88", "status": "draft"})
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    recorder = S1RuntimeDirectusRecorder(client=fake)

    result_payload = {
        "provider": "modal",
        "metadata": {},
        "artifacts": [
            {
                "artifact_type": "dataset_manifest",
                "storage_path": str(manifest_path),
                "content_type": "application/json",
                "metadata_json": {},
            }
        ],
    }

    recorder.record_job(
        service_name="s1_image",
        job_id="job-888",
        status="completed",
        input_payload={"identity_id": "88", "prompt": "test prompt"},
        result_payload=result_payload,
    )

    assert result_payload["metadata"]["dataset_storage_mode"] == "directus_rows"
    assert result_payload["metadata"]["persisted_artifacts"][0]["role"] == "dataset_manifest"
    assert result_payload["metadata"]["persisted_artifacts"][0]["file_id"] is None


def test_recorder_materializes_base_image_from_runtime_artifact_inline_payload(tmp_path: Path) -> None:
    fake = FakeControlPlane()
    identity = fake.create_item("s1_identities", {"avatar_id": "99", "status": "draft"})
    recorder = S1RuntimeDirectusRecorder(client=fake)
    png_payload = tiny_png_bytes()
    package_path = tmp_path / "dataset-99.zip"
    manifest = _build_dataset_manifest("99", package_path=package_path)
    result_payload = {
        "provider": "modal",
        "workflow_id": "base-image-ipadapter-impact",
        "workflow_version": "2026-04-03",
        "dataset_manifest": manifest,
        "metadata": {
            "seed_bundle": {"portrait_seed": 1, "variation_seed": 2, "dataset_seed": 3},
            "prompt": "real modal image",
            "negative_prompt": "bad anatomy",
            "workflow_id": "base-image-ipadapter-impact",
            "workflow_version": "2026-04-03",
            "base_model_id": "flux-schnell-v1",
        },
        "artifacts": [
            {
                "artifact_type": "base_image",
                "uri": "/opt/comfyui/output/vb/base_00001_.png",
                "content_type": "image/png",
                "metadata_json": {
                    "inline_data_base64": base64.b64encode(png_payload).decode("ascii"),
                },
            }
        ],
        "dataset_artifacts": [
            {
                "artifact_type": "base_image",
                "storage_path": "/app/data/artifacts/99/base-image.png",
                "content_type": "image/png",
                "metadata_json": {
                    "identity_id": "99",
                    "character_id": "99",
                },
            }
        ]
    }
    tmp_package = tmp_path / "dataset-99-materialized.zip"
    manifest["dataset_package_path"] = str(tmp_package)
    _write_dataset_package(tmp_package, manifest)
    result_payload["artifacts"].extend(
        [
            {
                "artifact_type": "dataset_manifest",
                "storage_path": str(tmp_package.with_suffix(".json")),
                "content_type": "application/json",
                "metadata_json": {},
            },
            {
                "artifact_type": "dataset_package",
                "storage_path": str(tmp_package),
                "content_type": "application/zip",
                "checksum_sha256": "abc123",
                "metadata_json": {},
            },
        ]
    )
    tmp_package.with_suffix(".json").write_text(json.dumps(manifest), encoding="utf-8")

    recorder.record_job(
        service_name="s1_image",
        job_id="job-321",
        status="completed",
        input_payload={"identity_id": "99", "prompt": "real modal image"},
        result_payload=result_payload,
    )

    base_artifact = fake.store["s1_artifacts"][0]
    assert base_artifact["role"] == "base_image"
    assert base_artifact["file"].startswith("file-")
    assert base_artifact["metadata_json"]["materialized_from_runtime_artifact"] is True
    assert len(fake.files) == 1
    assert identity["pipeline_state"] == "dataset_ready"
    assert identity["dataset_status"] == "ready"
    assert identity["latest_base_image_file_id"] == base_artifact["file"]
    assert result_payload["metadata"]["persisted_artifacts"][0]["persistence_target"] == "directus_file"
    assert base_artifact["metadata_json"]["registration_status"] == "registered"
    tmp_package.unlink(missing_ok=True)
    tmp_package.with_suffix(".json").unlink(missing_ok=True)


def test_recorder_reads_identity_id_from_metadata(tmp_path: Path) -> None:
    fake = FakeControlPlane()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    recorder = S1RuntimeDirectusRecorder(client=fake)

    recorder.record_job(
        service_name="s1_image",
        job_id="job-555",
        status="completed",
        input_payload={"metadata": {"identity_id": "meta-identity"}, "prompt": "test prompt"},
        result_payload={
            "provider": "modal",
            "metadata": {},
            "artifacts": [
                {
                    "artifact_type": "dataset_manifest",
                    "storage_path": str(manifest_path),
                    "content_type": "application/json",
                    "metadata_json": {},
                }
            ],
        },
    )

    assert fake.store["s1_generation_runs"][0]["identity_id"] == "meta-identity"


def test_recorder_blocks_training_when_dataset_validation_fails(tmp_path: Path) -> None:
    fake = FakeControlPlane()
    identity = fake.create_item("s1_identities", {"avatar_id": "blocked", "status": "draft", "pipeline_state": "base_images_registered"})
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "identity_id": "blocked",
        "sample_count": 8,
        "generated_samples": 8,
            "files": [{"path": "images/SFW/sample-001.png", "class_name": "SFW"}],
        "seed_bundle": {"portrait_seed": 1, "variation_seed": 2},
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    recorder = S1RuntimeDirectusRecorder(client=fake)

    recorder.record_job(
        service_name="s1_image",
        job_id="job-blocked",
        status="completed",
        input_payload={"identity_id": "blocked", "prompt": "test prompt"},
        result_payload={
            "provider": "modal",
            "workflow_version": "2026-04-02",
            "dataset_manifest": manifest,
            "metadata": {},
            "artifacts": [
                {
                    "artifact_type": "dataset_manifest",
                    "storage_path": str(manifest_path),
                    "content_type": "application/json",
                    "metadata_json": {},
                }
            ],
        },
    )

    validation_artifact = next(item for item in fake.store["s1_artifacts"] if item["role"] == "dataset_validation_report")
    assert validation_artifact["metadata_json"]["validation_status"] == "no_apto"
    assert identity["dataset_status"] == "rejected"
    assert identity["pipeline_state"] == "base_images_generated"
    assert any(event["event_type"] == "dataset_validation_failed" for event in fake.store["s1_events"])
