from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request
from uuid import uuid4
import zipfile

import pytest

from vixenbliss_creator.s1_control import validate_s1_dataset
from vixenbliss_creator.s1_control.support import tiny_png_bytes


def _build_manifest(identity_id: str, package_path: Path, *, sample_count: int = 40) -> dict:
    files = []
    sample_index = 0
    for framing, per_angle_count in (("close_up_face", 2), ("medium", 2), ("full_body", 4)):
        for camera_angle in ("front", "left_three_quarter", "right_three_quarter", "left_profile", "right_profile"):
            for class_name, wardrobe_state in (("SFW", "clothed"), ("NSFW", "nude")):
                iterations = 1 if framing != "full_body" else 2
                for full_body_variant in range(iterations):
                    if framing != "full_body" and class_name == "NSFW" and per_angle_count == 2 and sample_index % 2 == 0:
                        pass
                    sample_index += 1
                    files.append(
                        {
                            "sample_id": f"dataset-abc123def456-{sample_index:03d}",
                            "path": f"images/{class_name}/{camera_angle}/sample-{sample_index:03d}.png",
                            "class_name": class_name,
                            "variation_group": framing,
                            "framing": framing,
                            "shot_type": framing,
                            "camera_angle": camera_angle,
                            "pose": "editorial_standing",
                            "pose_family": "editorial_standing" if framing != "full_body" else f"full_body_pose_{full_body_variant + 1}",
                            "expression": "calm confident expression",
                            "wardrobe_state": wardrobe_state,
                            "prompt": f"adult real person {framing} {camera_angle} {wardrobe_state}",
                            "negative_prompt": "cgi, illustration, anime, duplicate body, text, watermark",
                            "caption": f"adult real person {framing} {camera_angle} {wardrobe_state} photorealistic reference photo",
                            "seed": sample_index,
                            "realism_profile": "photorealistic_adult_reference_v1",
                            "source_strategy": "avatar_prompt_plus_shot_plan_v1",
                        }
                    )
                    if len(files) == sample_count:
                        break
                if len(files) == sample_count:
                    break
            if len(files) == sample_count:
                break
        if len(files) == sample_count:
            break
    return {
        "schema_version": "1.1.0",
        "identity_id": identity_id,
        "sample_count": sample_count,
        "generated_samples": sample_count,
        "dataset_package_path": str(package_path),
        "files": files,
        "composition": {"policy": "balanced_50_50", "SFW": sample_count // 2, "NSFW": sample_count // 2},
        "seed_bundle": {"portrait_seed": 1, "variation_seed": 2, "dataset_seed": 3},
        "workflow_id": "base-image-ipadapter-impact",
        "workflow_version": "2026-04-08",
        "base_model_id": "flux-schnell-v1",
        "realism_profile": "photorealistic_adult_reference_v1",
        "source_strategy": "avatar_prompt_plus_shot_plan_v1",
    }


def _write_package(path: Path, manifest: dict, *, duplicate_payload: bool = False) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("dataset-manifest.json", json.dumps(manifest))
        for index, file_entry in enumerate(manifest["files"], start=1):
            payload = tiny_png_bytes()
            if not duplicate_payload:
                payload = payload + f"-{index}".encode("ascii")
            archive.writestr(file_entry["path"], payload)


def test_validator_accepts_dataset_that_meets_minimum_thresholds(tmp_path: Path) -> None:
    package_path = tmp_path / "dataset.zip"
    manifest = _build_manifest("42", package_path)
    _write_package(package_path, manifest)

    result = validate_s1_dataset(
        identity_id="42",
        run_id="run-1",
        result_payload={
            "dataset_manifest": manifest,
            "dataset_package_path": str(package_path),
            "base_model_id": "flux-schnell-v1",
            "workflow_id": "base-image-ipadapter-impact",
            "workflow_version": "2026-04-08",
        },
        runtime_metadata={"seed_bundle": manifest["seed_bundle"]},
        uploaded_artifacts=[
            {"artifact_type": "base_image", "storage_path": str(tmp_path / "base.png"), "directus_asset_url": "https://directus.example.com/assets/file-1"},
            {"artifact_type": "dataset_package", "storage_path": str(package_path)},
        ],
        identity_snapshot={"latest_base_model_id": "flux-schnell-v1"},
        current_pipeline_state="base_images_registered",
    )

    assert result.validation_status == "apto"
    assert result.dataset_status == "ready"
    assert result.pipeline_state == "dataset_ready"
    assert result.reasons == []


def test_validator_rejects_missing_prompt_metadata_and_package_files(tmp_path: Path) -> None:
    package_path = tmp_path / "dataset.zip"
    manifest = {
        "identity_id": "42",
        "sample_count": 12,
        "generated_samples": 12,
        "files": [{"path": "images/SFW/sample-001.png", "class_name": "SFW"}],
        "seed_bundle": {"portrait_seed": 1, "variation_seed": 2},
    }
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("dataset-manifest.json", json.dumps(manifest))

    result = validate_s1_dataset(
        identity_id="42",
        run_id="run-2",
        result_payload={"dataset_manifest": manifest, "dataset_package_path": str(package_path)},
        runtime_metadata={},
        uploaded_artifacts=[{"artifact_type": "dataset_package", "storage_path": str(package_path)}],
        identity_snapshot=None,
        current_pipeline_state="base_images_generated",
    )

    assert result.validation_status == "no_apto"
    codes = {reason["code"] for reason in result.reasons}
    assert "manifest_version_missing" in codes
    assert "seed_bundle_incomplete" in codes
    assert "dataset_package_missing_files" in codes


def test_validator_accepts_remote_dataset_package_locator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    identity_id = str(uuid4())
    package_path = tmp_path / "dataset.zip"
    manifest = _build_manifest(identity_id, Path("https://directus.example.com/assets/dataset-99.zip"))
    _write_package(package_path, manifest)
    package_bytes = package_path.read_bytes()

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self) -> bytes:
            return package_bytes

    def fake_urlopen(req: Request, timeout: int):
        assert req.full_url == "https://directus.example.com/assets/dataset-99.zip"
        return FakeResponse()

    monkeypatch.setattr("vixenbliss_creator.s1_control.dataset_validator.urlopen", fake_urlopen)

    result = validate_s1_dataset(
        identity_id=identity_id,
        run_id="run-remote",
        result_payload={
            "dataset_manifest": manifest,
            "dataset_package_path": "https://directus.example.com/assets/dataset-99.zip",
            "base_model_id": "flux-schnell-v1",
            "workflow_id": "base-image-ipadapter-impact",
            "workflow_version": "2026-04-08",
        },
        runtime_metadata={"seed_bundle": manifest["seed_bundle"]},
        uploaded_artifacts=[
            {"artifact_type": "base_image", "directus_asset_url": "https://directus.example.com/assets/file-1"},
            {"artifact_type": "dataset_package", "uri": "https://directus.example.com/assets/dataset-99.zip"},
        ],
        identity_snapshot={"latest_base_model_id": "flux-schnell-v1"},
        current_pipeline_state="base_images_registered",
    )

    assert result.validation_status == "apto"


def test_validator_rejects_duplicate_dominant_dataset_payloads(tmp_path: Path) -> None:
    package_path = tmp_path / "dataset.zip"
    manifest = _build_manifest("42", package_path)
    _write_package(package_path, manifest, duplicate_payload=True)

    result = validate_s1_dataset(
        identity_id="42",
        run_id="run-duplicates",
        result_payload={
            "dataset_manifest": manifest,
            "dataset_package_path": str(package_path),
            "base_model_id": "flux-schnell-v1",
            "workflow_id": "base-image-ipadapter-impact",
            "workflow_version": "2026-04-08",
        },
        runtime_metadata={"seed_bundle": manifest["seed_bundle"]},
        uploaded_artifacts=[
            {"artifact_type": "base_image", "directus_asset_url": "https://directus.example.com/assets/file-1"},
            {"artifact_type": "dataset_package", "storage_path": str(package_path)},
        ],
        identity_snapshot={"latest_base_model_id": "flux-schnell-v1"},
        current_pipeline_state="base_images_registered",
    )

    assert result.validation_status == "no_apto"
    assert any(reason["code"] == "dataset_payload_duplicates" for reason in result.reasons)


def test_validator_accepts_structural_dataset_when_package_locator_is_not_publicly_resolvable(tmp_path: Path) -> None:
    manifest = _build_manifest("42", Path("/app/data/artifacts/42/dataset-package.zip"), sample_count=40)

    result = validate_s1_dataset(
        identity_id="42",
        run_id="run-unreachable",
        result_payload={
            "dataset_manifest": manifest,
            "dataset_package_path": "/app/data/artifacts/42/dataset-package.zip",
            "base_model_id": "flux-schnell-v1",
            "workflow_id": "base-image-ipadapter-impact",
            "workflow_version": "2026-04-08",
        },
        runtime_metadata={"seed_bundle": manifest["seed_bundle"]},
        uploaded_artifacts=[
            {"artifact_type": "base_image", "directus_asset_url": "https://directus.example.com/assets/file-1"},
            {"artifact_type": "dataset_package", "storage_path": "/app/data/artifacts/42/dataset-package.zip"},
        ],
        identity_snapshot={"latest_base_model_id": "flux-schnell-v1"},
        current_pipeline_state="base_images_registered",
    )

    assert result.validation_status == "apto"
    assert result.dataset_status == "ready"
    assert result.metrics["dataset_package_verifiable"] is False
