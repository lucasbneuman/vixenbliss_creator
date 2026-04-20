from __future__ import annotations

from uuid import uuid4

import pytest

from vixenbliss_creator.agentic.models import GraphState
from vixenbliss_creator.agentic.runner import run_agentic_brain
from vixenbliss_creator.contracts.identity import TechnicalSheet
from vixenbliss_creator.s1_control import (
    build_identity_alias,
    build_identity_from_graph_state,
    build_identity_from_technical_sheet,
)


def test_build_identity_from_graph_state_materializes_identity_created_payload() -> None:
    state = run_agentic_brain("Creá un avatar nuevo para lifestyle premium")

    identity = build_identity_from_graph_state(state)

    assert identity.pipeline_state == "identity_created"
    assert identity.status == "draft"
    assert identity.base_model_id == "flux-schnell-v1"
    display_name = identity.technical_sheet_json.identity_core.display_name
    assert display_name
    assert identity.alias == build_identity_alias(display_name)
    assert identity.allowed_content_modes == ["sfw", "sensual", "nsfw"]
    assert identity.technical_sheet_json.identity_core.display_name == display_name


def test_build_identity_from_graph_state_requires_succeeded_graph_state() -> None:
    with pytest.raises(ValueError, match="succeeded"):
        build_identity_from_graph_state(GraphState(input_idea="idea de prueba suficientemente larga"))


def test_build_identity_alias_normalizes_accents_and_symbols() -> None:
    assert build_identity_alias("Ámbar Élite! 2026") == "ambar_elite_2026"


def test_build_identity_from_technical_sheet_falls_back_to_generated_uuid() -> None:
    state = run_agentic_brain("Creá un avatar nuevo para lifestyle premium")
    payload = state.final_technical_sheet_payload.model_dump(mode="json")
    payload["identity_metadata"]["avatar_id"] = "avatar_velvet_ember"
    payload["identity_core"]["display_name"] = "Ámbar Élite! 2026"
    technical_sheet = TechnicalSheet.model_validate(payload)

    identity = build_identity_from_technical_sheet(
        technical_sheet,
        identity_id=None,
        base_model_id="flux-schnell-v1",
    )

    assert identity.id
    assert identity.id != uuid4()
    assert identity.alias == "ambar_elite_2026"
