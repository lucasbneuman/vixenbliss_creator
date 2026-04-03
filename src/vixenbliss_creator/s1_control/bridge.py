from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import S1ControlSettings
from .directus import ControlPlanePort, DirectusControlPlaneClient


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


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
        identity_id = _stringify(input_payload.get("identity_id"))
        runtime_metadata = result_payload.get("metadata", {}) if isinstance(result_payload, dict) else {}
        run_payload = {
            "identity_id": identity_id,
            "run_type": service_name,
            "status": "running" if status == "in_progress" else status,
            "provider": result_payload.get("provider", "modal") if isinstance(result_payload, dict) else "modal",
            "external_job_id": job_id,
            "input_idea": input_payload.get("idea") or input_payload.get("prompt"),
            "result_json": result_payload or {},
            "error_message": error_message,
            "prompt_request_id": _stringify(input_payload.get("prompt_request_id")),
        }
        existing_run_id = _stringify(input_payload.get("directus_run_id"))
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
            self.client.create_item(
                "s1_artifacts",
                {
                    "identity_id": identity_id,
                    "run_id": run_id,
                    "role": artifact.get("artifact_type") or artifact.get("role"),
                    "file": artifact.get("directus_file_id"),
                    "uri": artifact.get("directus_asset_url") or artifact.get("storage_path") or artifact.get("uri"),
                    "content_type": artifact.get("content_type"),
                    "version": result_payload.get("workflow_version") or result_payload.get("training_manifest", {}).get("version"),
                    "metadata_json": self._artifact_metadata(artifact),
                },
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
        return run

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
            storage_path = artifact_copy.get("storage_path") or artifact_copy.get("uri")
            if not isinstance(storage_path, str):
                persisted.append(artifact_copy)
                continue
            source = Path(storage_path)
            if not source.exists() or not source.is_file():
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
                artifact_copy.setdefault("metadata_json", {})
                artifact_copy["metadata_json"]["directus_upload_error"] = str(exc)
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
                persisted.append(artifact_copy)
                continue
            artifact_copy["directus_file_id"] = upload["id"]
            artifact_copy["directus_asset_url"] = upload.get("asset_url") or upload.get("locator")
            artifact_copy["directus_storage"] = upload.get("storage")
            artifact_copy["storage_path"] = str(upload.get("locator") or upload.get("asset_url") or storage_path)
            artifact_copy.setdefault("metadata_json", {})
            artifact_copy["metadata_json"].update(
                {
                    "directus_file_id": upload["id"],
                    "directus_asset_url": upload.get("asset_url") or upload.get("locator"),
                    "directus_storage": upload.get("storage"),
                    "original_storage_path": storage_path,
                    "size_bytes": upload.get("filesize") or source.stat().st_size,
                    "artifact_kind": artifact_copy.get("artifact_type") or artifact_copy.get("role"),
                }
            )
            persisted.append(artifact_copy)

        result_payload["persisted_artifacts"] = persisted
        result_payload.setdefault("metadata", {})
        if any(item.get("directus_file_id") for item in persisted):
            result_payload["metadata"]["dataset_storage_mode"] = "directus_files"
        else:
            result_payload["metadata"].setdefault("dataset_storage_mode", "local_artifact_root")
        return persisted

    def _artifact_metadata(self, artifact: dict[str, Any]) -> dict[str, Any]:
        metadata = dict(artifact.get("metadata_json", {}))
        if artifact.get("directus_file_id"):
            metadata.setdefault("directus_file_id", artifact.get("directus_file_id"))
            metadata.setdefault("directus_asset_url", artifact.get("directus_asset_url"))
            metadata.setdefault("directus_storage", artifact.get("directus_storage"))
        if artifact.get("checksum_sha256"):
            metadata.setdefault("checksum_sha256", artifact.get("checksum_sha256"))
        if artifact.get("artifact_type"):
            metadata.setdefault("artifact_kind", artifact.get("artifact_type"))
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
        reference_artifact = next((item for item in uploaded_artifacts if (item.get("artifact_type") or item.get("role")) == "base_image"), None)
        dataset_manifest_artifact = next((item for item in uploaded_artifacts if (item.get("artifact_type") or item.get("role")) == "dataset_manifest"), None)
        dataset_package_artifact = next((item for item in uploaded_artifacts if (item.get("artifact_type") or item.get("role")) == "dataset_package"), None)
        generation_manifest = result_payload.get("generation_manifest") or result_payload.get("dataset_manifest") or {}
        seed_bundle = dict(runtime_metadata.get("seed_bundle") or generation_manifest.get("seed_bundle") or {})
        visual_config = {
            "prompt": runtime_metadata.get("prompt") or input_payload.get("prompt"),
            "negative_prompt": runtime_metadata.get("negative_prompt") or input_payload.get("negative_prompt"),
            "width": runtime_metadata.get("width") or input_payload.get("width"),
            "height": runtime_metadata.get("height") or input_payload.get("height"),
            "ip_adapter": runtime_metadata.get("ip_adapter") or input_payload.get("ip_adapter") or {},
            "face_detailer": runtime_metadata.get("face_detailer") or input_payload.get("face_detailer") or {},
            "reference_face_image_url": runtime_metadata.get("reference_face_image_url") or input_payload.get("reference_face_image_url"),
            "face_detection_confidence": result_payload.get("face_detection_confidence"),
            "dataset_storage_mode": runtime_metadata.get("dataset_storage_mode"),
            "persisted_artifacts": [
                {
                    "role": item.get("artifact_type") or item.get("role"),
                    "file_id": item.get("directus_file_id"),
                    "uri": item.get("directus_asset_url") or item.get("storage_path") or item.get("uri"),
                }
                for item in uploaded_artifacts
            ],
        }
        snapshot_payload = {
            "avatar_id": identity_id,
            "last_run_id": run_id,
            "reference_face_image_id": reference_artifact.get("directus_file_id") if isinstance(reference_artifact, dict) else None,
            "latest_generation_manifest_json": generation_manifest,
            "latest_seed_bundle_json": seed_bundle,
            "latest_visual_config_json": visual_config,
            "latest_base_model_id": runtime_metadata.get("base_model_id") or result_payload.get("base_model_id") or input_payload.get("base_model_id"),
            "latest_workflow_id": runtime_metadata.get("workflow_id") or result_payload.get("workflow_id") or input_payload.get("workflow_id"),
            "latest_workflow_version": runtime_metadata.get("workflow_version") or result_payload.get("workflow_version") or input_payload.get("workflow_version"),
            "latest_dataset_manifest_file_id": dataset_manifest_artifact.get("directus_file_id") if isinstance(dataset_manifest_artifact, dict) else None,
            "latest_dataset_package_file_id": dataset_package_artifact.get("directus_file_id") if isinstance(dataset_package_artifact, dict) else None,
        }
        identity_item = self._resolve_identity_item(identity_id)
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
