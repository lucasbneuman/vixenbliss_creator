from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from uuid import UUID, uuid4

from vixenbliss_creator.agentic.models import CompletionStatus, GraphState
from vixenbliss_creator.contracts.common import utc_now
from vixenbliss_creator.contracts.identity import Identity, IdentityStatus, PipelineState, TechnicalSheet


def _coerce_identity_id(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        try:
            return UUID(value)
        except ValueError:
            return None
    return None


def build_identity_alias(display_name: str, *, avatar_id: str | None = None) -> str:
    normalized = unicodedata.normalize("NFKD", display_name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    alias = re.sub(r"[^a-z0-9]+", "_", ascii_only).strip("_")
    alias = re.sub(r"_+", "_", alias)[:40].strip("_")
    if len(alias) >= 3:
        return alias

    fallback_suffix = "identity"
    if avatar_id:
        avatar_token = re.sub(r"[^a-z0-9]+", "", avatar_id.lower())
        if avatar_token:
            fallback_suffix = avatar_token[:12]
    return f"vb_{fallback_suffix}"[:40]


def build_identity_from_technical_sheet(
    technical_sheet: TechnicalSheet,
    *,
    identity_id: UUID | None = None,
    alias: str | None = None,
    base_model_id: str,
    reference_face_image_url: str | None = None,
    status: IdentityStatus = IdentityStatus.DRAFT,
    pipeline_state: PipelineState = PipelineState.IDENTITY_CREATED,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Identity:
    resolved_id = identity_id or _coerce_identity_id(technical_sheet.identity_metadata.avatar_id) or uuid4()
    resolved_alias = alias or build_identity_alias(
        technical_sheet.identity_core.display_name,
        avatar_id=technical_sheet.identity_metadata.avatar_id,
    )
    created = created_at or utc_now()
    updated = updated_at or created
    return Identity.model_validate(
        {
            "id": str(resolved_id),
            "alias": resolved_alias,
            "status": status,
            "pipeline_state": pipeline_state,
            "vertical": technical_sheet.identity_metadata.vertical,
            "allowed_content_modes": technical_sheet.operational_limits.allowed_content_modes,
            "reference_face_image_url": reference_face_image_url,
            "base_image_urls": [],
            "dataset_storage_path": None,
            "dataset_status": "not_started",
            "base_model_id": base_model_id,
            "lora_model_path": None,
            "lora_version": None,
            "technical_sheet_json": technical_sheet.model_dump(mode="json"),
            "created_at": created,
            "updated_at": updated,
        }
    )


def build_identity_from_graph_state(
    state: GraphState,
    *,
    identity_id: UUID | None = None,
    alias: str | None = None,
    base_model_id: str | None = None,
    reference_face_image_url: str | None = None,
    status: IdentityStatus = IdentityStatus.DRAFT,
    pipeline_state: PipelineState = PipelineState.IDENTITY_CREATED,
) -> Identity:
    if state.completion_status != CompletionStatus.SUCCEEDED:
        raise ValueError("GraphState must be succeeded before materializing an Identity payload")
    if state.final_technical_sheet_payload is None:
        raise ValueError("GraphState must include final_technical_sheet_payload before materializing an Identity payload")

    resolved_base_model_id = base_model_id or (
        state.copilot_recommendation.base_model_id if state.copilot_recommendation is not None else None
    )
    if not resolved_base_model_id:
        raise ValueError("base_model_id is required to materialize an Identity payload")

    return build_identity_from_technical_sheet(
        state.final_technical_sheet_payload,
        identity_id=identity_id,
        alias=alias,
        base_model_id=resolved_base_model_id,
        reference_face_image_url=reference_face_image_url,
        status=status,
        pipeline_state=pipeline_state,
    )
