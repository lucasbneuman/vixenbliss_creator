from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import zipfile

from vixenbliss_creator.contracts.identity import DatasetStatus, PipelineState


MIN_VALID_IMAGES = 12
MIN_BASE_IMAGES = 1
MIN_VARIATION_GROUPS = 3
MAX_DOMINANT_COMPOSITION_SHARE = 0.60
REQUIRED_SEED_KEYS = ("portrait_seed", "variation_seed", "dataset_seed")
REQUIRED_TRAINING_KEYS = ("identity_id", "base_model_id", "workflow_id", "workflow_version")
VARIATION_KEYS = ("variation_group", "framing", "shot_type", "camera_angle", "pose", "class_name")


@dataclass(frozen=True)
class DatasetValidationResult:
    validation_status: str
    dataset_status: str
    pipeline_state: str
    reasons: list[dict[str, Any]]
    metrics: dict[str, Any]
    report: dict[str, Any]

    @property
    def is_ready(self) -> bool:
        return self.dataset_status == DatasetStatus.READY.value


def _artifact_role(artifact: dict[str, Any]) -> str | None:
    role = artifact.get("artifact_type") or artifact.get("role")
    return str(role) if role is not None else None


def _artifact_uri(artifact: dict[str, Any]) -> str | None:
    uri = artifact.get("directus_asset_url") or artifact.get("storage_path") or artifact.get("uri")
    return str(uri) if uri is not None else None


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _reason(code: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "blocking",
        "message": message,
        "details": details or {},
    }


def _local_path(locator: str | None) -> Path | None:
    if not locator:
        return None
    candidate = Path(locator)
    if candidate.exists() and candidate.is_file():
        return candidate
    return None


def _remote_path(locator: str | None) -> Path | None:
    if not locator:
        return None
    parts = urlsplit(locator)
    if parts.scheme not in {"http", "https"}:
        return None
    headers: dict[str, str] = {}
    directus_base_url = os.getenv("DIRECTUS_BASE_URL")
    directus_token = os.getenv("DIRECTUS_API_TOKEN")
    if directus_base_url and directus_token:
        directus_parts = urlsplit(directus_base_url)
        if parts.scheme == directus_parts.scheme and parts.netloc == directus_parts.netloc:
            headers["Authorization"] = f"Bearer {directus_token}"
    request = Request(locator, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=20) as response:
            payload = response.read()
    except Exception:
        return None
    fd, raw_path = tempfile.mkstemp(prefix="vb-dataset-verify-", suffix=".zip")
    os.close(fd)
    path = Path(raw_path)
    path.write_bytes(payload)
    return path


def validate_s1_dataset(
    *,
    identity_id: str,
    run_id: str,
    result_payload: dict[str, Any],
    runtime_metadata: dict[str, Any],
    uploaded_artifacts: list[dict[str, Any]],
    identity_snapshot: dict[str, Any] | None,
    current_pipeline_state: str,
) -> DatasetValidationResult:
    # The validator is intentionally deterministic: if the package cannot be
    # resolved from the persisted locator, we reject the handoff instead of
    # silently trusting runtime-local state that downstream jobs cannot replay.
    reasons: list[dict[str, Any]] = []
    dataset_manifest = result_payload.get("dataset_manifest")
    manifest = dataset_manifest if isinstance(dataset_manifest, dict) else {}
    seed_bundle = dict(runtime_metadata.get("seed_bundle") or manifest.get("seed_bundle") or {})
    base_image_artifacts = [artifact for artifact in uploaded_artifacts if _artifact_role(artifact) == "base_image"]
    dataset_package_artifact = next((artifact for artifact in uploaded_artifacts if _artifact_role(artifact) == "dataset_package"), None)
    dataset_package_locator = (
        _artifact_uri(dataset_package_artifact)
        if isinstance(dataset_package_artifact, dict)
        else _stringify(result_payload.get("dataset_package_path") or manifest.get("dataset_package_path"))
    )
    dataset_package_path = _local_path(dataset_package_locator) or _remote_path(dataset_package_locator)
    files = manifest.get("files") if isinstance(manifest.get("files"), list) else []
    sample_count = int(manifest.get("sample_count") or 0)
    generated_samples = int(manifest.get("generated_samples") or 0)

    if not manifest:
        reasons.append(_reason("manifest_missing", "dataset_manifest is required before S1 Training"))
    else:
        manifest_version = _stringify(manifest.get("schema_version") or manifest.get("manifest_version") or manifest.get("version"))
        if not manifest_version:
            reasons.append(_reason("manifest_version_missing", "dataset_manifest must include a versioned manifest identifier"))

    if not dataset_package_locator:
        reasons.append(_reason("dataset_package_missing", "dataset_package locator is required before S1 Training"))
    elif dataset_package_path is None:
        reasons.append(
            _reason(
                "dataset_package_unreachable",
                "dataset_package locator must resolve to an accessible file for deterministic validation",
                details={"dataset_package_locator": dataset_package_locator},
            )
        )

    for key in REQUIRED_SEED_KEYS:
        if seed_bundle.get(key) is None:
            reasons.append(_reason("seed_bundle_incomplete", f"seed_bundle missing required key '{key}'"))

    trainer_metadata = {
        "identity_id": _stringify(manifest.get("identity_id") or identity_id),
        "base_model_id": _stringify(
            manifest.get("base_model_id")
            or runtime_metadata.get("base_model_id")
            or result_payload.get("base_model_id")
            or (identity_snapshot or {}).get("base_model_id")
            or (identity_snapshot or {}).get("latest_base_model_id")
        ),
        "workflow_id": _stringify(
            manifest.get("workflow_id")
            or runtime_metadata.get("workflow_id")
            or result_payload.get("workflow_id")
            or (identity_snapshot or {}).get("latest_workflow_id")
        ),
        "workflow_version": _stringify(
            manifest.get("workflow_version")
            or runtime_metadata.get("workflow_version")
            or result_payload.get("workflow_version")
            or (identity_snapshot or {}).get("latest_workflow_version")
        ),
    }
    for key in REQUIRED_TRAINING_KEYS:
        if not trainer_metadata.get(key):
            reasons.append(_reason("training_metadata_missing", f"training metadata missing required field '{key}'"))

    if sample_count < MIN_VALID_IMAGES:
        reasons.append(
            _reason(
                "sample_count_too_low",
                f"dataset requires at least {MIN_VALID_IMAGES} images",
                details={"sample_count": sample_count, "minimum_required": MIN_VALID_IMAGES},
            )
        )
    if generated_samples and generated_samples != len(files):
        reasons.append(
            _reason(
                "generated_samples_mismatch",
                "generated_samples must match the number of files declared in dataset_manifest",
                details={"generated_samples": generated_samples, "files_count": len(files)},
            )
        )
    if files and len(files) != sample_count:
        reasons.append(
            _reason(
                "manifest_files_mismatch",
                "sample_count must match the number of files declared in dataset_manifest",
                details={"sample_count": sample_count, "files_count": len(files)},
            )
        )

    base_image_count = len([artifact for artifact in base_image_artifacts if _artifact_uri(artifact)])
    if base_image_count < MIN_BASE_IMAGES:
        reasons.append(_reason("base_image_missing", "dataset must keep at least one registered base image"))

    variation_values = {
        str(file_entry[key]).strip().lower()
        for file_entry in files
        if isinstance(file_entry, dict)
        for key in VARIATION_KEYS
        if file_entry.get(key)
    }
    # We accept several metadata keys here so the gate can work with current
    # manifests and with future richer composition descriptors without changing
    # the blocking rule itself.
    if len(variation_values) < MIN_VARIATION_GROUPS:
        reasons.append(
            _reason(
                "variation_coverage_too_low",
                f"dataset requires at least {MIN_VARIATION_GROUPS} declared variation groups",
                details={"variation_values": sorted(variation_values), "minimum_required": MIN_VARIATION_GROUPS},
            )
        )

    composition = manifest.get("composition") if isinstance(manifest.get("composition"), dict) else {}
    composition_counts = {
        key: int(value)
        for key, value in composition.items()
        if key != "policy" and isinstance(value, int | float)
    }
    if not composition_counts and files:
        derived: dict[str, int] = {}
        for file_entry in files:
            class_name = _stringify(file_entry.get("class_name")) or "unclassified"
            derived[class_name] = derived.get(class_name, 0) + 1
        composition_counts = derived
    if composition_counts:
        total = sum(composition_counts.values())
        dominant_share = (max(composition_counts.values()) / total) if total else 1.0
        if dominant_share > MAX_DOMINANT_COMPOSITION_SHARE:
            reasons.append(
                _reason(
                    "composition_too_skewed",
                    "dataset composition is too concentrated in a single bucket",
                    details={
                        "composition_counts": composition_counts,
                        "dominant_share": dominant_share,
                        "max_allowed_share": MAX_DOMINANT_COMPOSITION_SHARE,
                    },
                )
            )

    archive_members: list[str] = []
    missing_files: list[str] = []
    if files:
        if dataset_package_path is not None:
            try:
                with zipfile.ZipFile(dataset_package_path) as archive:
                    archive_members = archive.namelist()
            except zipfile.BadZipFile:
                reasons.append(
                    _reason(
                        "dataset_package_invalid",
                        "dataset_package must be a readable zip file",
                        details={"dataset_package_locator": dataset_package_locator},
                    )
                )
            else:
                declared_paths = [str(file_entry.get("path")) for file_entry in files if isinstance(file_entry, dict) and file_entry.get("path")]
                missing_files = [path for path in declared_paths if path not in archive_members]
                if missing_files:
                    reasons.append(
                        _reason(
                            "dataset_package_missing_files",
                            "dataset_package is missing files declared in dataset_manifest",
                            details={"missing_files": missing_files[:10], "missing_count": len(missing_files)},
                        )
                    )
                if "dataset-manifest.json" not in archive_members:
                    reasons.append(_reason("dataset_package_missing_manifest", "dataset_package must include dataset-manifest.json"))
        else:
            reasons.append(_reason("dataset_package_not_verifiable", "dataset_package could not be verified against manifest file declarations"))
    if dataset_package_path is not None and dataset_package_path.name.startswith("vb-dataset-verify-"):
        dataset_package_path.unlink(missing_ok=True)

    validation_status = "apto" if not reasons else "no_apto"
    dataset_status = DatasetStatus.READY.value if not reasons else DatasetStatus.REJECTED.value
    pipeline_state = PipelineState.DATASET_READY.value if not reasons else current_pipeline_state
    metrics = {
        "sample_count": sample_count,
        "files_count": len(files),
        "base_image_count": base_image_count,
        "variation_group_count": len(variation_values),
        "composition_counts": composition_counts,
        "dataset_package_locator": dataset_package_locator,
        "archive_members_count": len(archive_members),
        "seed_bundle_keys": sorted(seed_bundle.keys()),
    }
    report = {
        "identity_id": identity_id,
        "run_id": run_id,
        "validation_status": validation_status,
        "dataset_status": dataset_status,
        "pipeline_state": pipeline_state,
        "reasons": reasons,
        "metrics": metrics,
        "required_thresholds": {
            "min_valid_images": MIN_VALID_IMAGES,
            "min_base_images": MIN_BASE_IMAGES,
            "min_variation_groups": MIN_VARIATION_GROUPS,
            "max_dominant_composition_share": MAX_DOMINANT_COMPOSITION_SHARE,
        },
        "training_metadata": trainer_metadata,
    }
    return DatasetValidationResult(
        validation_status=validation_status,
        dataset_status=dataset_status,
        pipeline_state=pipeline_state,
        reasons=reasons,
        metrics=metrics,
        report=report,
    )
