from __future__ import annotations

import base64
import copy
import json
import os
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vixenbliss_creator.contracts.identity import DatasetStatus, PipelineState

from .base_image_registry import S1BaseImageRegistry
from .config import S1ControlSettings
from .dataset_validator import validate_s1_dataset
from .directus import ControlPlanePort, DirectusControlPlaneClient
from .support import sha256_hex


DIRECTUS_FILE_ARTIFACT_ROLES = {"base_image", "generated_image", "thumbnail"}


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _input_value(input_payload: dict[str, Any], key: str) -> Any:
    if key in input_payload:
        return input_payload.get(key)
    metadata = input_payload.get("metadata")
    if isinstance(metadata, dict):
        return metadata.get(key)
    return None


def _artifact_role(artifact: dict[str, Any]) -> str | None:
    role = artifact.get("artifact_type") or artifact.get("role")
    return str(role) if role is not None else None


def _artifact_uri(artifact: dict[str, Any]) -> str | None:
    uri = artifact.get("directus_asset_url") or artifact.get("storage_path") or artifact.get("uri")
    return str(uri) if uri is not None else None


def _artifact_persists_as_file(artifact: dict[str, Any]) -> bool:
    role = _artifact_role(artifact)
    if role in DIRECTUS_FILE_ARTIFACT_ROLES:
        return True
    content_type = str(artifact.get("content_type") or "").lower()
    return content_type.startswith("image/")


def _artifact_temp_suffix(artifact: dict[str, Any]) -> str:
    role = _artifact_role(artifact)
    if role in {"base_image", "generated_image", "thumbnail"}:
        return ".png"
    if role == "dataset_manifest":
        return ".json"
    if role == "dataset_package":
        return ".zip"
    return Path(str(artifact.get("storage_path") or artifact.get("uri") or "artifact")).suffix or ".bin"


def _artifact_inline_payload(artifact: dict[str, Any]) -> str | None:
    metadata = artifact.get("metadata_json", {}) or {}
    inline_data = metadata.get("inline_data_base64")
    if isinstance(inline_data, str) and inline_data:
        return inline_data
    return None


@dataclass
class S1RuntimeDirectusRecorder:
    client: ControlPlanePort

    @classmethod
    def from_settings(cls, settings: S1ControlSettings) -> "S1RuntimeDirectusRecorder":
        return cls(client=DirectusControlPlaneClient(settings))

    def record_job(
        self,
        *,
        service_name: str,
        job_id: str,
        status: str,
        input_payload: dict[str, Any],
        result_payload: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        identity_id = _stringify(_input_value(input_payload, "identity_id"))
        sanitized_initial_result = self._sanitize_result_payload(result_payload)
        run_payload = {
            "identity_id": identity_id,
            "run_type": service_name,
            "status": "running" if status == "in_progress" else status,
            "provider": result_payload.get("provider", "modal") if isinstance(result_payload, dict) else "modal",
            "external_job_id": job_id,
            "input_idea": _input_value(input_payload, "idea") or _input_value(input_payload, "prompt"),
            "result_json": sanitized_initial_result or {},
            "error_message": error_message,
            "prompt_request_id": _stringify(_input_value(input_payload, "prompt_request_id")),
        }
        existing_run_id = _stringify(_input_value(input_payload, "directus_run_id"))
        if existing_run_id:
            run = self.client.update_item("s1_generation_runs", existing_run_id, run_payload)
        else:
            run = self.client.create_item("s1_generation_runs", run_payload)
        run_id = str(run["id"])
        uploaded_artifacts = self._persist_artifacts(
            identity_id=identity_id,
            run_id=run_id,
            service_name=service_name,
            result_payload=result_payload,
        )
        runtime_metadata = result_payload.get("metadata", {}) if isinstance(result_payload, dict) else {}
        artifact_rows: list[dict[str, Any]] = []
        self.client.create_item(
            "s1_events",
            {
                "identity_id": identity_id,
                "run_id": run_id,
                "event_type": "runtime_job_recorded",
                "message": f"{service_name} job {job_id} recorded in Directus",
                "payload_json": {"status": status},
                "created_by": service_name,
            },
        )
        if not isinstance(result_payload, dict):
            return run
        for artifact in uploaded_artifacts:
            artifact_rows.append(
                self.client.create_item(
                    "s1_artifacts",
                    {
                        "identity_id": identity_id,
                        "run_id": run_id,
                        "role": _artifact_role(artifact),
                        "file": artifact.get("directus_file_id"),
                        "uri": _artifact_uri(artifact),
                        "content_type": artifact.get("content_type"),
                        "version": result_payload.get("workflow_version")
                        or result_payload.get("training_manifest", {}).get("version"),
                        "metadata_json": self._artifact_metadata(artifact),
                    },
                )
            )
        self._update_identity_snapshot(
            identity_id=identity_id,
            run_id=run_id,
            service_name=service_name,
            input_payload=input_payload,
            result_payload=result_payload,
            uploaded_artifacts=uploaded_artifacts,
            runtime_metadata=runtime_metadata,
        )
        if identity_id and service_name == "s1_image":
            # Runtime persistence marks the identity as base_images_generated first.
            # Formal registration happens afterwards once we have recoverable assets,
            # checksums, and traceability metadata for the uploaded base images.
            S1BaseImageRegistry(client=self.client).register(
                identity_id=identity_id,
                run_id=run_id,
                source_job_id=job_id,
                result_payload=result_payload,
                runtime_metadata=runtime_metadata,
                uploaded_artifacts=uploaded_artifacts,
                artifact_rows=artifact_rows,
            )
            self._record_dataset_validation(
                identity_id=identity_id,
                run_id=run_id,
                result_payload=result_payload,
                runtime_metadata=runtime_metadata,
                uploaded_artifacts=uploaded_artifacts,
            )
        training_manifest = result_payload.get("training_manifest")
        if isinstance(training_manifest, dict):
            self.client.create_item(
                "s1_model_assets",
                {
                    "identity_id": identity_id,
                    "asset_type": "lora_model",
                    "provider": result_payload.get("provider", "modal"),
                    "model_id": training_manifest.get("trigger_word") or training_manifest.get("result_manifest_path"),
                    "version": training_manifest.get("model_registry", {}).get("version_name") or "v1",
                    "storage_path": training_manifest.get("lora_model_path"),
                    "status": "ready",
                    "metadata_json": training_manifest,
                },
            )
        if isinstance(result_payload, dict):
            self.client.update_item(
                "s1_generation_runs",
                run_id,
                {
                    "status": "running" if status == "in_progress" else status,
                    "result_json": self._sanitize_result_payload(result_payload),
                    "error_message": error_message,
                },
            )
        return run

    @staticmethod
    def _persisted_artifact_summary(artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            "role": _artifact_role(artifact),
            "file_id": artifact.get("directus_file_id"),
            "uri": _artifact_uri(artifact),
            "storage": artifact.get("directus_storage"),
            "persistence_target": artifact.get("persistence_target"),
            "checksum_sha256": artifact.get("checksum_sha256"),
        }

    @staticmethod
    def _sanitize_result_payload(result_payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(result_payload, dict):
            return result_payload

        def sanitize(value: Any) -> Any:
            if isinstance(value, dict):
                sanitized: dict[str, Any] = {}
                for key, item in value.items():
                    if key == "inline_data_base64" and isinstance(item, str):
                        sanitized[key] = f"[omitted base64 payload: {len(item)} chars]"
                    else:
                        sanitized[key] = sanitize(item)
                return sanitized
            if isinstance(value, list):
                return [sanitize(item) for item in value]
            return value

        return sanitize(copy.deepcopy(result_payload))

    def _persist_artifacts(
        self,
        *,
        identity_id: str | None,
        run_id: str,
        service_name: str,
        result_payload: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if not isinstance(result_payload, dict):
            return []
        upload_candidates = result_payload.get("dataset_artifacts") or result_payload.get("artifacts") or []
        persisted: list[dict[str, Any]] = []
        for artifact in upload_candidates:
            artifact_copy = dict(artifact)
            artifact_copy.setdefault("metadata_json", {})
            storage_path = artifact_copy.get("storage_path") or artifact_copy.get("uri")
            source, cleanup_path = self._materialize_artifact_source(artifact_copy, result_payload)
            if source is None:
                artifact_copy.setdefault("persistence_target", "directus_row")
                persisted.append(artifact_copy)
                continue
            artifact_copy["metadata_json"].update(
                {
                    "original_storage_path": storage_path,
                    "size_bytes": source.stat().st_size,
                    "artifact_kind": _artifact_role(artifact_copy),
                    "checksum_sha256": artifact_copy.get("checksum_sha256") or sha256_hex(source.read_bytes()),
                }
            )
            if not _artifact_persists_as_file(artifact_copy):
                artifact_copy["persistence_target"] = "directus_row"
                if cleanup_path is not None and cleanup_path.exists():
                    cleanup_path.unlink(missing_ok=True)
                persisted.append(artifact_copy)
                continue
            try:
                upload = self.client.upload_file(
                    source,
                    file_name=source.name,
                    content_type=artifact_copy.get("content_type"),
                    title=f"{service_name}:{artifact_copy.get('artifact_type') or artifact_copy.get('role') or source.name}",
                )
            except Exception as exc:
                artifact_copy["metadata_json"]["directus_upload_error"] = str(exc)
                artifact_copy["persistence_target"] = "directus_row"
                self.client.create_item(
                    "s1_events",
                    {
                        "identity_id": identity_id,
                        "run_id": run_id,
                        "event_type": "runtime_artifact_upload_failed",
                        "message": f"Failed to persist {source.name} in Directus Files",
                        "payload_json": {"storage_path": storage_path, "error": str(exc)},
                        "created_by": service_name,
                    },
                )
                if cleanup_path is not None and cleanup_path.exists():
                    cleanup_path.unlink(missing_ok=True)
                persisted.append(artifact_copy)
                continue
            artifact_copy["directus_file_id"] = upload["id"]
            artifact_copy["directus_asset_url"] = upload.get("asset_url") or upload.get("locator")
            artifact_copy["directus_storage"] = upload.get("storage")
            artifact_copy["storage_path"] = str(upload.get("locator") or upload.get("asset_url") or storage_path)
            artifact_copy["persistence_target"] = "directus_file"
            artifact_copy["metadata_json"].update(
                {
                    "directus_file_id": upload["id"],
                    "directus_asset_url": upload.get("asset_url") or upload.get("locator"),
                    "directus_storage": upload.get("storage"),
                    "size_bytes": upload.get("filesize") or source.stat().st_size,
                }
            )
            if cleanup_path is not None and cleanup_path.exists():
                cleanup_path.unlink(missing_ok=True)
            persisted.append(artifact_copy)

        result_payload["persisted_artifacts"] = persisted
        result_payload.setdefault("metadata", {})
        result_payload["metadata"]["persisted_artifacts"] = [
            self._persisted_artifact_summary(item) for item in persisted
        ]
        has_file_artifacts = any(item.get("directus_file_id") for item in persisted)
        has_row_artifacts = any(item.get("persistence_target") == "directus_row" for item in persisted)
        if has_file_artifacts and has_row_artifacts:
            result_payload["metadata"]["dataset_storage_mode"] = "directus_images_and_rows"
        elif has_file_artifacts:
            result_payload["metadata"]["dataset_storage_mode"] = "directus_files"
        elif has_row_artifacts:
            result_payload["metadata"]["dataset_storage_mode"] = "directus_rows"
        else:
            result_payload["metadata"].setdefault("dataset_storage_mode", "local_artifact_root")
        return persisted

    def _materialize_artifact_source(
        self,
        artifact: dict[str, Any],
        result_payload: dict[str, Any] | None,
    ) -> tuple[Path | None, Path | None]:
        storage_path = artifact.get("storage_path") or artifact.get("uri")
        if isinstance(storage_path, str):
            source = Path(storage_path)
            if source.exists() and source.is_file():
                return source, None

        role = _artifact_role(artifact)
        inline_data = _artifact_inline_payload(artifact)
        if role in DIRECTUS_FILE_ARTIFACT_ROLES:
            if inline_data:
                temp_path = self._write_temp_file(base64.b64decode(inline_data), suffix=_artifact_temp_suffix(artifact))
                return temp_path, temp_path
            runtime_artifact = self._find_runtime_artifact_source(role=role, result_payload=result_payload, artifact=artifact)
            if runtime_artifact is not None:
                runtime_inline_data = _artifact_inline_payload(runtime_artifact)
                if runtime_inline_data:
                    artifact.setdefault("metadata_json", {})
                    artifact["metadata_json"]["materialized_from_runtime_artifact"] = True
                    temp_path = self._write_temp_file(
                        base64.b64decode(runtime_inline_data),
                        suffix=_artifact_temp_suffix(runtime_artifact),
                    )
                    return temp_path, temp_path

        if role == "dataset_manifest" and isinstance(result_payload, dict):
            manifest = result_payload.get("dataset_manifest")
            if isinstance(manifest, dict):
                temp_path = self._write_temp_file(
                    json.dumps(manifest, indent=2).encode("utf-8"),
                    suffix=".json",
                )
                artifact.setdefault("storage_path", str(temp_path))
                return temp_path, temp_path

        if role == "dataset_package" and isinstance(result_payload, dict):
            package_path = self._rebuild_dataset_package(result_payload)
            if package_path is not None:
                artifact.setdefault("metadata_json", {})
                artifact["metadata_json"].update(
                    {
                        "package_entries": ["images/base-image.png", "dataset-manifest.json"],
                        "package_contains_base_image_png": True,
                    }
                )
                artifact.setdefault("storage_path", str(package_path))
                return package_path, package_path

        return None, None

    @staticmethod
    def _find_runtime_artifact_source(
        *,
        role: str | None,
        result_payload: dict[str, Any] | None,
        artifact: dict[str, Any],
    ) -> dict[str, Any] | None:
        if role is None or not isinstance(result_payload, dict):
            return None
        candidates = result_payload.get("artifacts") or []
        for candidate in candidates:
            if candidate is artifact:
                continue
            if _artifact_role(candidate) != role:
                continue
            if _artifact_inline_payload(candidate):
                return candidate
            source = candidate.get("storage_path") or candidate.get("uri")
            if isinstance(source, str):
                path = Path(source)
                if path.exists() and path.is_file():
                    return candidate
        return None

    def _rebuild_dataset_package(self, result_payload: dict[str, Any]) -> Path | None:
        manifest = result_payload.get("dataset_manifest")
        if not isinstance(manifest, dict):
            return None
        artifacts = result_payload.get("artifacts") or result_payload.get("dataset_artifacts") or []
        base_image = next((item for item in artifacts if _artifact_role(item) == "base_image"), None)
        if not isinstance(base_image, dict):
            return None
        inline_data = (base_image.get("metadata_json") or {}).get("inline_data_base64")
        if not isinstance(inline_data, str) or not inline_data:
            return None

        fd, raw_path = tempfile.mkstemp(prefix="vb-dataset-package-", suffix=".zip")
        try:
            os.close(fd)
        except OSError:
            pass
        Path(raw_path).unlink(missing_ok=True)
        package_path = Path(raw_path)
        base_image_bytes = base64.b64decode(inline_data)
        with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("images/base-image.png", base_image_bytes)
            archive.writestr("dataset-manifest.json", json.dumps(manifest, indent=2))
        return package_path

    @staticmethod
    def _write_temp_file(payload: bytes, *, suffix: str) -> Path:
        fd, raw_path = tempfile.mkstemp(prefix="vb-artifact-", suffix=suffix)
        path = Path(raw_path)
        try:
            os.close(fd)
        except OSError:
            pass
        with path.open("wb") as handle:
            handle.write(payload)
        return path

    def _artifact_metadata(self, artifact: dict[str, Any]) -> dict[str, Any]:
        metadata = dict(artifact.get("metadata_json", {}))
        metadata.setdefault("persistence_target", artifact.get("persistence_target") or "directus_row")
        if artifact.get("directus_file_id"):
            metadata.setdefault("directus_file_id", artifact.get("directus_file_id"))
            metadata.setdefault("directus_asset_url", artifact.get("directus_asset_url"))
            metadata.setdefault("directus_storage", artifact.get("directus_storage"))
        if artifact.get("checksum_sha256"):
            metadata.setdefault("checksum_sha256", artifact.get("checksum_sha256"))
        role = _artifact_role(artifact)
        if role:
            metadata.setdefault("artifact_kind", role)
        return metadata

    def _update_identity_snapshot(
        self,
        *,
        identity_id: str | None,
        run_id: str,
        service_name: str,
        input_payload: dict[str, Any],
        result_payload: dict[str, Any],
        uploaded_artifacts: list[dict[str, Any]],
        runtime_metadata: dict[str, Any],
    ) -> None:
        if service_name != "s1_image" or not identity_id or not isinstance(result_payload, dict):
            return
        base_image_artifact = next((item for item in uploaded_artifacts if _artifact_role(item) == "base_image"), None)
        base_image_artifacts = [item for item in uploaded_artifacts if _artifact_role(item) == "base_image"]
        dataset_manifest_artifact = next((item for item in uploaded_artifacts if _artifact_role(item) == "dataset_manifest"), None)
        dataset_package_artifact = next((item for item in uploaded_artifacts if _artifact_role(item) == "dataset_package"), None)
        generation_manifest = result_payload.get("generation_manifest") or result_payload.get("dataset_manifest") or {}
        dataset_manifest = result_payload.get("dataset_manifest") or {}
        seed_bundle = dict(runtime_metadata.get("seed_bundle") or generation_manifest.get("seed_bundle") or {})
        character_id = _stringify(_input_value(input_payload, "character_id")) or identity_id
        visual_config = {
            "character_id": character_id,
            "prompt": runtime_metadata.get("prompt") or input_payload.get("prompt"),
            "negative_prompt": runtime_metadata.get("negative_prompt") or input_payload.get("negative_prompt"),
            "width": runtime_metadata.get("width") or input_payload.get("width"),
            "height": runtime_metadata.get("height") or input_payload.get("height"),
            "ip_adapter": runtime_metadata.get("ip_adapter") or input_payload.get("ip_adapter") or {},
            "face_detailer": runtime_metadata.get("face_detailer") or input_payload.get("face_detailer") or {},
            "reference_face_image_url": runtime_metadata.get("reference_face_image_url") or input_payload.get("reference_face_image_url"),
            "face_detection_confidence": result_payload.get("face_detection_confidence"),
            "dataset_storage_mode": runtime_metadata.get("dataset_storage_mode"),
            "persisted_artifacts": runtime_metadata.get("persisted_artifacts", []),
        }
        base_image_uri = _artifact_uri(base_image_artifact) if isinstance(base_image_artifact, dict) else None
        base_image_urls = [_artifact_uri(item) for item in base_image_artifacts if _artifact_uri(item)]
        has_dataset_handoff = bool(
            _artifact_uri(dataset_package_artifact) if isinstance(dataset_package_artifact, dict) else result_payload.get("dataset_package_path")
        )
        snapshot_payload = {
            "avatar_id": identity_id,
            "last_run_id": run_id,
            "pipeline_state": PipelineState.BASE_IMAGES_GENERATED.value,
            "reference_face_image_id": _stringify(_input_value(input_payload, "reference_face_image_id")),
            "reference_face_image_url": visual_config["reference_face_image_url"],
            "base_image_urls": base_image_urls or ([base_image_uri] if base_image_uri else []),
            "dataset_storage_path": _artifact_uri(dataset_package_artifact) if isinstance(dataset_package_artifact, dict) else result_payload.get("dataset_package_path"),
            "dataset_status": DatasetStatus.IN_PROGRESS.value if has_dataset_handoff else DatasetStatus.NOT_STARTED.value,
            "latest_generation_manifest_json": generation_manifest,
            "latest_seed_bundle_json": seed_bundle,
            "latest_visual_config_json": visual_config,
            "base_model_id": runtime_metadata.get("base_model_id") or result_payload.get("base_model_id") or input_payload.get("base_model_id"),
            "latest_base_model_id": runtime_metadata.get("base_model_id") or result_payload.get("base_model_id") or input_payload.get("base_model_id"),
            "latest_workflow_id": runtime_metadata.get("workflow_id") or result_payload.get("workflow_id") or input_payload.get("workflow_id"),
            "latest_workflow_version": runtime_metadata.get("workflow_version") or result_payload.get("workflow_version") or input_payload.get("workflow_version"),
            "latest_base_image_file_id": base_image_artifact.get("directus_file_id") if isinstance(base_image_artifact, dict) else None,
            "latest_dataset_manifest_json": dataset_manifest,
            "latest_dataset_package_uri": _artifact_uri(dataset_package_artifact) if isinstance(dataset_package_artifact, dict) else result_payload.get("dataset_package_path"),
            "latest_dataset_manifest_file_id": dataset_manifest_artifact.get("directus_file_id") if isinstance(dataset_manifest_artifact, dict) else None,
            "latest_dataset_package_file_id": dataset_package_artifact.get("directus_file_id") if isinstance(dataset_package_artifact, dict) else None,
        }
        identity_item = self._resolve_identity_item(identity_id)
        if identity_item is None:
            self.client.create_item("s1_identities", snapshot_payload)
            return
        self.client.update_item("s1_identities", str(identity_item["id"]), snapshot_payload)

    def _record_dataset_validation(
        self,
        *,
        identity_id: str,
        run_id: str,
        result_payload: dict[str, Any],
        runtime_metadata: dict[str, Any],
        uploaded_artifacts: list[dict[str, Any]],
    ) -> None:
        identity_item = self._resolve_identity_item(identity_id)
        current_pipeline_state = _stringify((identity_item or {}).get("pipeline_state")) or PipelineState.BASE_IMAGES_GENERATED.value
        # Validation owns the dataset_ready promotion. Recording artifacts or
        # registering base images is not enough to unlock training anymore.
        validation = validate_s1_dataset(
            identity_id=identity_id,
            run_id=run_id,
            result_payload=result_payload,
            runtime_metadata=runtime_metadata,
            uploaded_artifacts=uploaded_artifacts,
            identity_snapshot=identity_item,
            current_pipeline_state=current_pipeline_state,
        )
        result_payload["dataset_validation"] = validation.report
        self.client.create_item(
            "s1_artifacts",
            {
                "identity_id": identity_id,
                "run_id": run_id,
                "role": "dataset_validation_report",
                "file": None,
                "uri": f"dataset-validation://{identity_id}/{run_id}",
                "content_type": "application/json",
                "version": result_payload.get("workflow_version") or runtime_metadata.get("workflow_version"),
                "metadata_json": validation.report,
            },
        )
        self.client.create_item(
            "s1_events",
            {
                "identity_id": identity_id,
                "run_id": run_id,
                "event_type": "dataset_validation_passed" if validation.is_ready else "dataset_validation_failed",
                "message": "Dataset validation passed" if validation.is_ready else "Dataset validation failed",
                "payload_json": validation.report,
                "created_by": "dataset_validator",
            },
        )
        snapshot_payload = {
            "avatar_id": identity_id,
            "dataset_status": validation.dataset_status,
            "pipeline_state": validation.pipeline_state,
            "last_run_id": run_id,
            "latest_visual_config_json": {
                **((identity_item or {}).get("latest_visual_config_json") or {}),
                "dataset_validation_status": validation.validation_status,
                "dataset_validation_report_uri": f"dataset-validation://{identity_id}/{run_id}",
            },
        }
        if identity_item is None:
            self.client.create_item("s1_identities", snapshot_payload)
            return
        self.client.update_item("s1_identities", str(identity_item["id"]), snapshot_payload)

    def _resolve_identity_item(self, identity_id: str) -> dict[str, Any] | None:
        matches = self.client.list_items(
            "s1_identities",
            params={"filter[avatar_id][_eq]": identity_id, "limit": "1"},
        )
        if matches:
            return matches[0]
        try:
            return self.client.read_item("s1_identities", identity_id)
        except Exception:
            return None
