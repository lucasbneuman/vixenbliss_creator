from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from vixenbliss_creator.contracts.identity import Identity

from .directus import ControlPlanePort


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _identity_to_item_payload(
    identity: Identity,
    *,
    created_by: str | None = None,
    source_prompt_request_id: str | None = None,
) -> dict[str, Any]:
    metadata = identity.technical_sheet_json.identity_metadata
    identity_core = identity.technical_sheet_json.identity_core
    payload = {
        "avatar_id": str(identity.id),
        "identity_schema_version": identity.schema_version,
        "alias": identity.alias,
        "display_name": identity_core.display_name,
        "category": metadata.category,
        "status": identity.status,
        "allowed_content_modes": identity.allowed_content_modes,
        "pipeline_state": identity.pipeline_state,
        "vertical": identity.vertical,
        "style": metadata.style,
        "occupation_or_content_basis": metadata.occupation_or_content_basis,
        "approved": False,
        "reference_face_image_url": _stringify(identity.reference_face_image_url),
        "base_image_urls": [_stringify(item) for item in identity.base_image_urls],
        "dataset_storage_path": identity.dataset_storage_path,
        "dataset_status": identity.dataset_status,
        "base_model_id": identity.base_model_id,
        "lora_model_path": identity.lora_model_path,
        "lora_version": identity.lora_version,
        "technical_sheet_json": identity.technical_sheet_json.model_dump(mode="json"),
        "created_at": identity.created_at.isoformat(),
        "updated_at": identity.updated_at.isoformat(),
        "latest_base_model_id": identity.base_model_id,
    }
    if created_by is not None:
        payload["created_by"] = created_by
    if source_prompt_request_id is not None:
        payload["source_prompt_request_id"] = source_prompt_request_id
    return payload


def _identity_from_item_payload(item: dict[str, Any]) -> Identity:
    return Identity.model_validate(
        {
            "schema_version": item["identity_schema_version"],
            "id": item["avatar_id"],
            "alias": item["alias"],
            "status": item["status"],
            "pipeline_state": item["pipeline_state"],
            "vertical": item["vertical"],
            "allowed_content_modes": item.get("allowed_content_modes", []),
            "reference_face_image_url": item.get("reference_face_image_url"),
            "base_image_urls": item.get("base_image_urls") or [],
            "dataset_storage_path": item.get("dataset_storage_path"),
            "dataset_status": item["dataset_status"],
            "base_model_id": item.get("base_model_id"),
            "lora_model_path": item.get("lora_model_path"),
            "lora_version": item.get("lora_version"),
            "technical_sheet_json": item["technical_sheet_json"],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
        }
    )


@dataclass
class DirectusIdentityStore:
    client: ControlPlanePort

    def upsert_identity(
        self,
        identity: Identity,
        *,
        created_by: str | None = None,
        source_prompt_request_id: str | None = None,
    ) -> Identity:
        payload = _identity_to_item_payload(
            identity,
            created_by=created_by,
            source_prompt_request_id=source_prompt_request_id,
        )
        existing = self._resolve_identity_row(identity.id)
        if existing is None:
            self.client.create_item("s1_identities", payload)
            return identity
        self.client.update_item("s1_identities", str(existing["id"]), payload)
        return identity

    def get_identity(self, identity_id: str | UUID) -> Identity | None:
        item = self._resolve_identity_row(identity_id)
        if item is None:
            return None
        return _identity_from_item_payload(item)

    def _resolve_identity_row(self, identity_id: str | UUID) -> dict[str, Any] | None:
        external_id = str(identity_id)
        matches = self.client.list_items(
            "s1_identities",
            params={"filter[avatar_id][_eq]": external_id, "limit": "1"},
        )
        if matches:
            return matches[0]
        try:
            item = self.client.read_item("s1_identities", external_id)
        except Exception:
            return None
        if str(item.get("avatar_id") or item.get("id")) != external_id:
            return None
        return item
