from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from vixenbliss_creator.contracts.model_registry import ModelRegistry

from .directus import ControlPlanePort


CATALOG_TIMESTAMP = datetime(2026, 4, 3, 0, 0, tzinfo=timezone.utc)


DEFAULT_S1_MODEL_CATALOG = (
    {
        "id": "7f4cf0a4-d8ea-4f6d-b0cf-8ec2e3082a10",
        "model_family": "flux",
        "model_role": "base_model",
        "provider": "black_forest_labs",
        "version_name": "flux-schnell-v1",
        "display_name": "Flux Schnell Base Image v1",
        "base_model_id": "flux-schnell-v1",
        "storage_path": "models/flux/schnell/v1/flux-schnell.safetensors",
        "parent_model_id": None,
        "compatibility_notes": "Compatible con ComfyUI para base image, LoRA, IP-Adapter y ControlNet. Video queda delegado a placeholder futuro.",
        "quantization": "none",
        "is_active": True,
        "metadata_json": {
            "pipelines_supported": ["s1_image", "s2_image"],
            "adapters_supported": ["lora", "ip_adapter", "controlnet"],
            "video_support": "placeholder_only",
            "version_policy": {
                "base_models": "version_name inmutable por familia",
                "loras": "derivadas del base_model_id con version por entrenamiento",
            },
        },
        "created_at": CATALOG_TIMESTAMP,
        "updated_at": CATALOG_TIMESTAMP,
        "deprecated_at": None,
    },
    {
        "id": "2fec6f38-8f08-44f8-8e0b-1dc1cbcdf0b2",
        "model_family": "future_video",
        "model_role": "video_placeholder",
        "provider": "internal",
        "version_name": "future-video-placeholder-v1",
        "display_name": "Future Video Placeholder v1",
        "base_model_id": "future-video-placeholder-v1",
        "storage_path": None,
        "parent_model_id": None,
        "compatibility_notes": "Contrato reservado para pipeline de video futuro. No persiste binario todavía y prepara compatibilidad declarativa.",
        "quantization": "none",
        "is_active": True,
        "metadata_json": {
            "pipelines_supported": ["s2_video_future"],
            "adapters_supported": ["planned_lora_reference"],
            "video_support": "planned",
            "version_policy": {
                "base_models": "placeholder hasta integrar proveedor real de video",
                "loras": "se validarán por compatibilidad explícita cuando exista runtime",
            },
        },
        "created_at": CATALOG_TIMESTAMP,
        "updated_at": CATALOG_TIMESTAMP,
        "deprecated_at": None,
    },
)


def default_model_catalog() -> list[ModelRegistry]:
    return [ModelRegistry.model_validate(payload) for payload in DEFAULT_S1_MODEL_CATALOG]


def _model_to_item_payload(model: ModelRegistry) -> dict[str, Any]:
    return {
        "model_id": str(model.id),
        "model_registry_schema_version": model.schema_version,
        "model_family": model.model_family,
        "model_role": model.model_role,
        "provider": model.provider,
        "version_name": model.version_name,
        "display_name": model.display_name,
        "base_model_id": model.base_model_id,
        "storage_path": model.storage_path,
        "parent_model_id": str(model.parent_model_id) if model.parent_model_id is not None else None,
        "compatibility_notes": model.compatibility_notes,
        "quantization": model.quantization,
        "is_active": model.is_active,
        "metadata_json": model.metadata_json,
        "created_at": model.created_at.isoformat(),
        "updated_at": model.updated_at.isoformat(),
        "deprecated_at": model.deprecated_at.isoformat() if model.deprecated_at is not None else None,
    }


def _model_from_item_payload(item: dict[str, Any]) -> ModelRegistry:
    return ModelRegistry.model_validate(
        {
            "schema_version": item["model_registry_schema_version"],
            "id": item["model_id"],
            "model_family": item["model_family"],
            "model_role": item["model_role"],
            "provider": item["provider"],
            "version_name": item["version_name"],
            "display_name": item["display_name"],
            "base_model_id": item.get("base_model_id"),
            "storage_path": item.get("storage_path"),
            "parent_model_id": item.get("parent_model_id"),
            "compatibility_notes": item.get("compatibility_notes"),
            "quantization": item["quantization"],
            "is_active": item["is_active"],
            "metadata_json": item.get("metadata_json") or {},
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
            "deprecated_at": item.get("deprecated_at"),
        }
    )


@dataclass
class DirectusModelRegistryStore:
    client: ControlPlanePort

    def upsert_model(self, model: ModelRegistry) -> ModelRegistry:
        payload = _model_to_item_payload(model)
        existing = self._resolve_model_row(model.id)
        if existing is None:
            self.client.create_item("s1_model_registry", payload)
            return model
        self.client.update_item("s1_model_registry", str(existing["id"]), payload)
        return model

    def get_model(self, model_id: str | UUID) -> ModelRegistry | None:
        item = self._resolve_model_row(model_id)
        if item is None:
            return None
        return _model_from_item_payload(item)

    def list_models(self, *, active_only: bool = False, model_role: str | None = None) -> list[ModelRegistry]:
        items = self.client.list_items("s1_model_registry")
        models = [_model_from_item_payload(item) for item in items]
        if active_only:
            models = [model for model in models if model.is_active]
        if model_role is not None:
            models = [model for model in models if model.model_role == model_role]
        return models

    def find_active_base_model(self, base_model_id: str) -> ModelRegistry | None:
        for model in self.list_models(active_only=True, model_role="base_model"):
            if model.base_model_id == base_model_id:
                return model
        return None

    def seed_default_catalog(self) -> list[ModelRegistry]:
        catalog = default_model_catalog()
        for model in catalog:
            self.upsert_model(model)
        return catalog

    def _resolve_model_row(self, model_id: str | UUID) -> dict[str, Any] | None:
        external_id = str(model_id)
        for item in self.client.list_items("s1_model_registry"):
            if str(item.get("model_id")) == external_id:
                return item
        return None
