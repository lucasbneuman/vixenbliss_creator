from __future__ import annotations

import json
from pathlib import Path
import zipfile

from vixenbliss_creator.s1_control import validate_s1_dataset
from vixenbliss_creator.s1_control.support import tiny_png_bytes


def _build_manifest(identity_id: str, package_path: Path, *, sample_count: int = 12) -> dict:
    files = []
    variation_cycle = ("close_up", "medium", "full_body")
    pose_cycle = ("front", "three_quarter", "profile")
    half = sample_count // 2
    sample_index = 0
    for class_name, count in (("with_clothes", half), ("without_clothes", half)):
        for class_offset in range(count):
            sample_index += 1
            variation_group = variation_cycle[(sample_index - 1) % len(variation_cycle)]
            files.append(
                {
                    "path": f"images/{class_name}/sample-{class_offset + 1:03d}.png",
                    "class_name": class_name,
                    "variation_group": variation_group,
                    "pose": pose_cycle[(sample_index - 1) % len(pose_cycle)],
                }
            )
    return {
        "schema_version": "1.0.0",
        "identity_id": identity_id,
        "sample_count": sample_count,
        "generated_samples": sample_count,
        "dataset_package_path": str(package_path),
        "files": files,
        "composition": {"policy": "balanced_50_50", "with_clothes": half, "without_clothes": half},
        "seed_bundle": {"portrait_seed": 1, "variation_seed": 2, "dataset_seed": 3},
        "workflow_id": "base-image-ipadapter-impact",
        "workflow_version": "2026-04-02",
        "base_model_id": "flux-schnell-v1",
    }


def _write_package(path: Path, manifest: dict) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("dataset-manifest.json", json.dumps(manifest))
        for file_entry in manifest["files"]:
            archive.writestr(file_entry["path"], tiny_png_bytes())


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
            "workflow_version": "2026-04-02",
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


def test_validator_rejects_missing_manifest_version_and_package_files(tmp_path: Path) -> None:
    package_path = tmp_path / "dataset.zip"
    manifest = {
        "identity_id": "42",
        "sample_count": 12,
        "generated_samples": 12,
        "files": [{"path": "images/with_clothes/sample-001.png", "class_name": "with_clothes"}],
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
