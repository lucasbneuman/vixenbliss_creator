from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from vixenbliss_creator.contracts.artifact import Artifact, ArtifactType
from vixenbliss_creator.contracts.identity import PipelineState

from .directus import ControlPlanePort
from .support import sha256_hex


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _artifact_role(artifact: dict[str, Any]) -> str | None:
    role = artifact.get("artifact_type") or artifact.get("role")
    return str(role) if role is not None else None


def _artifact_uri(artifact: dict[str, Any]) -> str | None:
    uri = artifact.get("directus_asset_url") or artifact.get("storage_path") or artifact.get("uri")
    return str(uri) if uri is not None else None


def _coerce_uuid_or_stable(value: str) -> str:
    try:
        return str(UUID(value))
    except ValueError:
        return str(uuid5(NAMESPACE_URL, value))


def _coerce_uuid_or_none(value: str) -> str | None:
    try:
        return str(UUID(value))
    except ValueError:
        return None


@dataclass
class BaseImageRegistrationResult:
    registered_rows: list[dict[str, Any]]
    primary_row: dict[str, Any]


@dataclass
class S1BaseImageRegistry:
    client: ControlPlanePort

    def register(
        self,
        *,
        identity_id: str,
        run_id: str,
        source_job_id: str,
        result_payload: dict[str, Any],
        runtime_metadata: dict[str, Any],
        uploaded_artifacts: list[dict[str, Any]],
        artifact_rows: list[dict[str, Any]],
    ) -> BaseImageRegistrationResult | None:
        # This is the canonical S1 handoff step: runtime persistence already happened,
        # and now we promote the uploaded base images into formally registered artifacts.
        base_pairs = [
            (artifact, row)
            for artifact, row in zip(uploaded_artifacts, artifact_rows, strict=False)
            if _artifact_role(artifact) == ArtifactType.BASE_IMAGE.value
        ]
        if not base_pairs:
            return None

        registered_rows: list[dict[str, Any]] = []
        for index, (artifact, row) in enumerate(base_pairs):
            prepared = self._prepare_registered_metadata(
                identity_id=identity_id,
                run_id=run_id,
                source_job_id=source_job_id,
                artifact=artifact,
                row=row,
                result_payload=result_payload,
                runtime_metadata=runtime_metadata,
                is_primary=index == 0,
            )
            if prepared is None:
                self._emit_registration_failure(
                    identity_id=identity_id,
                    run_id=run_id,
                    row=row,
                    reason="base image is missing recoverable uri, directus file id or checksum",
                )
                return None
            registered_rows.append(
                self.client.update_item(
                    "s1_artifacts",
                    str(row["id"]),
                    {
                        "uri": prepared["uri"],
                        "file": prepared["file"],
                        "content_type": prepared["content_type"],
                        "version": prepared["version"],
                        "metadata_json": prepared["metadata_json"],
                    },
                )
            )

        primary_row = registered_rows[0]
        self._update_identity_snapshot(
            identity_id=identity_id,
            run_id=run_id,
            registered_rows=registered_rows,
            primary_row=primary_row,
            result_payload=result_payload,
            runtime_metadata=runtime_metadata,
        )
        self.client.create_item(
            "s1_events",
            {
                "identity_id": identity_id,
                "run_id": run_id,
                "event_type": "base_images_registered",
                "message": f"Registered {len(registered_rows)} base image artifacts",
                "payload_json": {
                    "artifact_ids": [str(row["id"]) for row in registered_rows],
                    "primary_file_id": primary_row.get("file"),
                },
                "created_by": "s1_image",
            },
        )
        return BaseImageRegistrationResult(registered_rows=registered_rows, primary_row=primary_row)

    def _prepare_registered_metadata(
        self,
        *,
        identity_id: str,
        run_id: str,
        source_job_id: str,
        artifact: dict[str, Any],
        row: dict[str, Any],
        result_payload: dict[str, Any],
        runtime_metadata: dict[str, Any],
        is_primary: bool,
    ) -> dict[str, Any] | None:
        uri = _artifact_uri(artifact) or _stringify(row.get("uri"))
        file_id = _stringify(artifact.get("directus_file_id") or row.get("file"))
        content_type = _stringify(artifact.get("content_type") or row.get("content_type"))
        metadata = dict(row.get("metadata_json") or {})
        metadata.update(artifact.get("metadata_json") or {})
        checksum = _stringify(metadata.get("checksum_sha256")) or self._checksum_from_source(artifact)
        size_bytes = metadata.get("size_bytes")
        if size_bytes is None:
            size_bytes = self._size_from_source(artifact)
        version = _stringify(
            result_payload.get("workflow_version") or runtime_metadata.get("workflow_version") or row.get("version")
        )
        if not uri or not file_id or not checksum or not content_type:
            return None

        prompt = runtime_metadata.get("prompt") or result_payload.get("dataset_manifest", {}).get("prompt")
        negative_prompt = runtime_metadata.get("negative_prompt") or result_payload.get("dataset_manifest", {}).get(
            "negative_prompt"
        )
        seed_bundle = dict(
            runtime_metadata.get("seed_bundle")
            or result_payload.get("dataset_manifest", {}).get("seed_bundle")
            or metadata.get("seed_bundle")
            or {}
        )
        # The strict Artifact contract uses UUIDs; Directus runtime rows may still carry
        # operational ids like "42" or "job-123", so we validate with stable UUID surrogates
        # and preserve the original ids in metadata_json for downstream consumers.
        artifact_payload = {
            "id": str(uuid4()),
            "identity_id": _coerce_uuid_or_stable(identity_id),
            "artifact_type": ArtifactType.BASE_IMAGE.value,
            "storage_path": uri,
            "source_job_id": _coerce_uuid_or_none(source_job_id),
            "base_model_id": runtime_metadata.get("base_model_id") or result_payload.get("base_model_id"),
            "model_version_used": version,
            "checksum_sha256": checksum,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "metadata_json": {
                **metadata,
                "artifact_schema_version": "1.0.0",
                "artifact_type": ArtifactType.BASE_IMAGE.value,
                "identity_id": identity_id,
                "source_job_id": source_job_id,
                "directus_run_id": run_id,
                "workflow_id": runtime_metadata.get("workflow_id") or result_payload.get("workflow_id"),
                "workflow_version": version,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "seed_bundle": seed_bundle,
                "is_primary_reference": is_primary,
                "registration_status": "registered",
            },
        }
        validated = Artifact.model_validate(artifact_payload)
        return {
            "uri": uri,
            "file": file_id,
            "content_type": content_type,
            "version": version,
            "metadata_json": validated.metadata_json,
        }

    def _update_identity_snapshot(
        self,
        *,
        identity_id: str,
        run_id: str,
        registered_rows: list[dict[str, Any]],
        primary_row: dict[str, Any],
        result_payload: dict[str, Any],
        runtime_metadata: dict[str, Any],
    ) -> None:
        identity_item = self._resolve_identity_item(identity_id)
        if identity_item is None:
            return
        base_image_urls = [row["uri"] for row in registered_rows if row.get("uri")]
        if not base_image_urls:
            return
        dataset_manifest = result_payload.get("dataset_manifest") or {}
        seed_bundle = dict(runtime_metadata.get("seed_bundle") or dataset_manifest.get("seed_bundle") or {})
        dataset_package_artifact = next(
            (item for item in result_payload.get("artifacts", []) if _artifact_role(item) == "dataset_package"),
            None,
        )
        dataset_package_locator = result_payload.get("dataset_package_path") or (
            _artifact_uri(dataset_package_artifact) if isinstance(dataset_package_artifact, dict) else None
        )
        self.client.update_item(
            "s1_identities",
            str(identity_item["id"]),
            {
                "avatar_id": identity_id,
                "last_run_id": run_id,
                "pipeline_state": PipelineState.BASE_IMAGES_REGISTERED.value,
                "base_image_urls": base_image_urls,
                "reference_face_image_url": primary_row["uri"],
                "reference_face_image_id": primary_row.get("file"),
                "latest_base_image_file_id": primary_row.get("file"),
                "latest_seed_bundle_json": seed_bundle,
                "dataset_storage_path": dataset_package_locator,
                "dataset_status": "in_progress" if dataset_package_locator else identity_item.get("dataset_status"),
                "latest_dataset_manifest_json": dataset_manifest,
                "latest_dataset_package_uri": dataset_package_locator,
                "latest_base_model_id": runtime_metadata.get("base_model_id") or result_payload.get("base_model_id"),
                "latest_workflow_id": runtime_metadata.get("workflow_id") or result_payload.get("workflow_id"),
                "latest_workflow_version": runtime_metadata.get("workflow_version") or result_payload.get("workflow_version"),
            },
        )

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

    def _emit_registration_failure(self, *, identity_id: str, run_id: str, row: dict[str, Any], reason: str) -> None:
        self.client.create_item(
            "s1_events",
            {
                "identity_id": identity_id,
                "run_id": run_id,
                "event_type": "base_images_registration_failed",
                "message": f"Failed to register base image artifact {row.get('id')}",
                "payload_json": {"artifact_id": row.get("id"), "reason": reason},
                "created_by": "s1_image",
            },
        )

    @staticmethod
    def _checksum_from_source(artifact: dict[str, Any]) -> str | None:
        source = artifact.get("storage_path") or artifact.get("uri")
        if not isinstance(source, str):
            return None
        path = Path(source)
        if not path.exists() or not path.is_file():
            return None
        return sha256_hex(path.read_bytes())

    @staticmethod
    def _size_from_source(artifact: dict[str, Any]) -> int | None:
        source = artifact.get("storage_path") or artifact.get("uri")
        if not isinstance(source, str):
            return None
        path = Path(source)
        if not path.exists() or not path.is_file():
            return None
        return path.stat().st_size
