from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import error, parse, request

from .config import S1ControlSettings


def _json_request(
    method: str,
    url: str,
    *,
    token: str,
    payload: dict[str, Any] | None = None,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method=method,
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP error calling {url}: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error calling {url}: {exc.reason}") from exc
    return {} if not raw else json.loads(raw)


class ControlPlanePort(Protocol):
    def create_item(self, collection: str, payload: dict[str, Any]) -> dict[str, Any]: ...

    def update_item(self, collection: str, item_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...

    def read_item(self, collection: str, item_id: str) -> dict[str, Any]: ...

    def list_items(self, collection: str, *, params: dict[str, str] | None = None) -> list[dict[str, Any]]: ...

    def delete_many(self, collection: str, *, filter_payload: dict[str, Any]) -> None: ...


@dataclass
class DirectusControlPlaneClient:
    settings: S1ControlSettings

    def create_item(self, collection: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = _json_request(
            "POST",
            f"{self.settings.directus_base_url}/items/{collection}",
            token=self.settings.directus_token,
            payload=payload,
            timeout_seconds=self.settings.directus_timeout_seconds,
        )
        return response["data"]

    def update_item(self, collection: str, item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = _json_request(
            "PATCH",
            f"{self.settings.directus_base_url}/items/{collection}/{item_id}",
            token=self.settings.directus_token,
            payload=payload,
            timeout_seconds=self.settings.directus_timeout_seconds,
        )
        return response["data"]

    def read_item(self, collection: str, item_id: str) -> dict[str, Any]:
        response = _json_request(
            "GET",
            f"{self.settings.directus_base_url}/items/{collection}/{item_id}",
            token=self.settings.directus_token,
            timeout_seconds=self.settings.directus_timeout_seconds,
        )
        return response["data"]

    def list_items(self, collection: str, *, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        url = f"{self.settings.directus_base_url}/items/{collection}"
        if params:
            url += "?" + parse.urlencode(params)
        response = _json_request(
            "GET",
            url,
            token=self.settings.directus_token,
            timeout_seconds=self.settings.directus_timeout_seconds,
        )
        return response.get("data", [])

    def delete_many(self, collection: str, *, filter_payload: dict[str, Any]) -> None:
        _json_request(
            "DELETE",
            f"{self.settings.directus_base_url}/items/{collection}",
            token=self.settings.directus_token,
            payload={"query": filter_payload},
            timeout_seconds=self.settings.directus_timeout_seconds,
        )


S1_DIRECTUS_SCHEMA: dict[str, dict[str, Any]] = {
    "s1_identities": {
        "meta": {"icon": "person", "note": "Registro maestro de identidades S1", "accountability": "all"},
        "fields": [
            {"field": "avatar_id", "type": "string"},
            {"field": "display_name", "type": "string"},
            {"field": "category", "type": "string"},
            {"field": "vertical", "type": "string"},
            {"field": "style", "type": "string"},
            {"field": "occupation_or_content_basis", "type": "text"},
            {"field": "status", "type": "string"},
            {"field": "approved", "type": "boolean"},
            {"field": "allowed_content_modes", "type": "json"},
            {"field": "pipeline_state", "type": "string"},
            {"field": "source_prompt_request_id", "type": "string"},
            {"field": "last_run_id", "type": "string"},
        ],
    },
    "s1_prompt_requests": {
        "meta": {"icon": "tips_and_updates", "note": "Ideas y constraints iniciales S1", "accountability": "all"},
        "fields": [
            {"field": "idea", "type": "text"},
            {"field": "manual_constraints_json", "type": "json"},
            {"field": "creation_mode", "type": "string"},
            {"field": "request_status", "type": "string"},
            {"field": "requested_by", "type": "string"},
            {"field": "identity_id", "type": "string"},
            {"field": "latest_run_id", "type": "string"},
        ],
    },
    "s1_generation_runs": {
        "meta": {"icon": "play_circle", "note": "Ejecuciones operativas del pipeline S1", "accountability": "all"},
        "fields": [
            {"field": "identity_id", "type": "string"},
            {"field": "prompt_request_id", "type": "string"},
            {"field": "run_type", "type": "string"},
            {"field": "status", "type": "string"},
            {"field": "started_at", "type": "timestamp"},
            {"field": "finished_at", "type": "timestamp"},
            {"field": "error_code", "type": "string"},
            {"field": "error_message", "type": "text"},
            {"field": "provider", "type": "string"},
            {"field": "external_job_id", "type": "string"},
            {"field": "input_idea", "type": "text"},
            {"field": "result_json", "type": "json"},
        ],
    },
    "s1_artifacts": {
        "meta": {"icon": "image", "note": "Artifacts visibles de S1", "accountability": "all"},
        "fields": [
            {"field": "identity_id", "type": "string"},
            {"field": "run_id", "type": "string"},
            {"field": "role", "type": "string"},
            {"field": "file", "type": "uuid"},
            {"field": "uri", "type": "string"},
            {"field": "content_type", "type": "string"},
            {"field": "version", "type": "string"},
            {"field": "metadata_json", "type": "json"},
        ],
    },
    "s1_model_assets": {
        "meta": {"icon": "inventory_2", "note": "Modelos base y LoRAs asociados a identidades", "accountability": "all"},
        "fields": [
            {"field": "identity_id", "type": "string"},
            {"field": "asset_type", "type": "string"},
            {"field": "provider", "type": "string"},
            {"field": "model_id", "type": "string"},
            {"field": "version", "type": "string"},
            {"field": "storage_path", "type": "string"},
            {"field": "status", "type": "string"},
            {"field": "metadata_json", "type": "json"},
        ],
    },
    "s1_events": {
        "meta": {"icon": "receipt_long", "note": "Auditoria operativa simple de S1", "accountability": "all"},
        "fields": [
            {"field": "identity_id", "type": "string"},
            {"field": "run_id", "type": "string"},
            {"field": "event_type", "type": "string"},
            {"field": "message", "type": "text"},
            {"field": "payload_json", "type": "json"},
            {"field": "created_by", "type": "string"},
        ],
    },
}


@dataclass
class DirectusSchemaManager:
    settings: S1ControlSettings

    def ensure_schema(self) -> list[str]:
        created: list[str] = []
        existing = {row["collection"] for row in self._list_collections()}
        for collection, definition in S1_DIRECTUS_SCHEMA.items():
            if collection not in existing:
                self._create_collection(collection, definition["meta"])
                created.append(collection)
            current_fields = {row["field"] for row in self._list_fields(collection)}
            for field in definition["fields"]:
                if field["field"] not in current_fields:
                    self._create_field(collection, field["field"], field["type"])
        return created

    def _list_collections(self) -> list[dict[str, Any]]:
        response = _json_request(
            "GET",
            f"{self.settings.directus_base_url}/collections",
            token=self.settings.directus_token,
            timeout_seconds=self.settings.directus_timeout_seconds,
        )
        return response.get("data", [])

    def _list_fields(self, collection: str) -> list[dict[str, Any]]:
        response = _json_request(
            "GET",
            f"{self.settings.directus_base_url}/fields/{collection}",
            token=self.settings.directus_token,
            timeout_seconds=self.settings.directus_timeout_seconds,
        )
        return response.get("data", [])

    def _create_collection(self, collection: str, meta: dict[str, Any]) -> None:
        _json_request(
            "POST",
            f"{self.settings.directus_base_url}/collections",
            token=self.settings.directus_token,
            payload={"collection": collection, "meta": meta, "schema": {"name": collection}},
            timeout_seconds=self.settings.directus_timeout_seconds,
        )

    def _create_field(self, collection: str, field_name: str, field_type: str) -> None:
        payload = {
            "field": field_name,
            "type": field_type,
            "meta": {"interface": "input", "special": None},
            "schema": {"name": field_name, "table": collection, "data_type": self._data_type_for(field_type)},
        }
        if field_type == "json":
            payload["meta"]["interface"] = "input-code"
            payload["meta"]["options"] = {"language": "json"}
        elif field_type == "boolean":
            payload["meta"]["interface"] = "boolean"
        elif field_type == "text":
            payload["meta"]["interface"] = "input-multiline"
        elif field_type == "timestamp":
            payload["meta"]["interface"] = "datetime"
        _json_request(
            "POST",
            f"{self.settings.directus_base_url}/fields/{collection}",
            token=self.settings.directus_token,
            payload=payload,
            timeout_seconds=self.settings.directus_timeout_seconds,
        )

    @staticmethod
    def _data_type_for(field_type: str) -> str:
        mapping = {
            "string": "varchar",
            "text": "text",
            "integer": "integer",
            "boolean": "boolean",
            "timestamp": "timestamp",
            "json": "json",
            "float": "float",
            "uuid": "uuid",
        }
        return mapping[field_type]
