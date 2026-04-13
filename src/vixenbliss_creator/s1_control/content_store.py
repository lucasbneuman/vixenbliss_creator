from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vixenbliss_creator.contracts.content import Content

from .directus import ControlPlanePort


def _content_to_item_payload(content: Content) -> dict[str, Any]:
    return {
        "content_id": content.id,
        "content_schema_version": content.schema_version,
        "identity_id": content.identity_id,
        "content_mode": content.content_mode,
        "video_generation_mode": content.video_generation_mode,
        "generation_status": content.generation_status,
        "qa_status": content.qa_status,
        "job_id": content.job_id,
        "primary_artifact_id": content.primary_artifact_id,
        "related_artifact_ids": content.related_artifact_ids,
        "base_model_id": content.base_model_id,
        "model_version_used": content.model_version_used,
        "provider": content.provider,
        "workflow_id": content.workflow_id,
        "prompt": content.prompt,
        "negative_prompt": content.negative_prompt,
        "seed": content.seed,
        "source_content_id": content.source_content_id,
        "source_artifact_id": content.source_artifact_id,
        "duration_seconds": content.duration_seconds,
        "frame_count": content.frame_count,
        "frame_rate": content.frame_rate,
        "metadata_json": content.metadata_json,
        "created_at": content.created_at.isoformat(),
        "updated_at": content.updated_at.isoformat(),
    }


def _content_from_item_payload(item: dict[str, Any]) -> Content:
    return Content.model_validate(
        {
            "schema_version": item["content_schema_version"],
            "id": item["content_id"],
            "identity_id": item["identity_id"],
            "content_mode": item["content_mode"],
            "video_generation_mode": item.get("video_generation_mode"),
            "generation_status": item["generation_status"],
            "qa_status": item["qa_status"],
            "job_id": item.get("job_id"),
            "primary_artifact_id": item.get("primary_artifact_id"),
            "related_artifact_ids": item.get("related_artifact_ids") or [],
            "base_model_id": item.get("base_model_id"),
            "model_version_used": item.get("model_version_used"),
            "provider": item.get("provider"),
            "workflow_id": item.get("workflow_id"),
            "prompt": item.get("prompt"),
            "negative_prompt": item.get("negative_prompt"),
            "seed": item.get("seed"),
            "source_content_id": item.get("source_content_id"),
            "source_artifact_id": item.get("source_artifact_id"),
            "duration_seconds": item.get("duration_seconds"),
            "frame_count": item.get("frame_count"),
            "frame_rate": item.get("frame_rate"),
            "metadata_json": item.get("metadata_json") or {},
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
        }
    )


@dataclass
class DirectusContentStore:
    client: ControlPlanePort

    def upsert_content(self, content: Content) -> Content:
        payload = _content_to_item_payload(content)
        existing = self._resolve_content_row(content.id)
        if existing is None:
            self.client.create_item("content_catalog", payload)
            return content
        self.client.update_item("content_catalog", str(existing["id"]), payload)
        return content

    def get_content(self, content_id: str) -> Content | None:
        item = self._resolve_content_row(content_id)
        if item is None:
            return None
        return _content_from_item_payload(item)

    def list_contents(self, *, identity_id: str | None = None) -> list[Content]:
        items = self.client.list_items("content_catalog")
        if identity_id is not None:
            items = [item for item in items if str(item.get("identity_id")) == str(identity_id)]
        return [_content_from_item_payload(item) for item in items]

    def _resolve_content_row(self, content_id: str) -> dict[str, Any] | None:
        for item in self.client.list_items("content_catalog"):
            if str(item.get("content_id")) == str(content_id):
                return item
        try:
            item = self.client.read_item("content_catalog", content_id)
        except Exception:
            return None
        if str(item.get("content_id") or item.get("id")) != str(content_id):
            return None
        return item
