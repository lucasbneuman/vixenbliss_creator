from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request

from fastapi import FastAPI, HTTPException
from pydantic import Field

from vixenbliss_creator.agentic.models import CopilotRecommendation, CopilotStage
from vixenbliss_creator.agentic.workflow_registry import ApprovedWorkflow, WorkflowRegistry
from vixenbliss_creator.contracts.common import ContractBaseModel


OPENAI_API_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_API_KEY = os.getenv("OPEN_AI_TOKEN") or os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
COPILOT_TIMEOUT_SECONDS = int(os.getenv("COMFYUI_COPILOT_TIMEOUT_SECONDS", "60"))
COPILOT_DEFAULT_STAGE = os.getenv("COMFYUI_COPILOT_DEFAULT_STAGE", CopilotStage.S1_IDENTITY_IMAGE.value)
workflow_registry = WorkflowRegistry.default()


class CopilotRequest(ContractBaseModel):
    stage: CopilotStage = CopilotStage.S1_IDENTITY_IMAGE
    expansion_summary: str = Field(min_length=8, max_length=600)
    prompt_blueprint: str = Field(min_length=8, max_length=2000)
    technical_sheet_payload: dict[str, Any]
    approved_workflows: list[ApprovedWorkflow] = Field(default_factory=list, max_length=12)


CopilotRequest.model_rebuild()


def _json_request(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout_seconds: int = COPILOT_TIMEOUT_SECONDS,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    req = request.Request(url=url, data=body, headers=request_headers, method=method)
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP error calling {url}: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error calling {url}: {exc.reason}") from exc
    return {} if not raw else json.loads(raw)


def _recommended_workflows(payload: CopilotRequest) -> list[ApprovedWorkflow]:
    if payload.approved_workflows:
        return payload.approved_workflows
    return workflow_registry.for_stage(payload.stage)


def _fallback_recommendation(payload: CopilotRequest, *, reason: str) -> CopilotRecommendation:
    recommendation = workflow_registry.build_fallback_recommendation(payload.stage)
    compatibility_notes = [*recommendation.compatibility_notes, f"Fallback reason: {reason}"][:12]
    return recommendation.model_copy(
        update={
            "prompt_template": payload.prompt_blueprint[:600],
            "reasoning_summary": f"OpenAI-assisted recommendation degraded to approved fallback: {reason}"[:320],
            "compatibility_notes": compatibility_notes,
            "registry_source": "modal_openai_fallback",
        }
    )


def _extract_json_text(response_payload: dict[str, Any]) -> dict[str, Any]:
    content = response_payload["choices"][0]["message"]["content"]
    if isinstance(content, str):
        return json.loads(content)
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return json.loads("\n".join(parts))
    raise RuntimeError("Unsupported OpenAI response content format")


def _build_messages(payload: CopilotRequest, approved_workflows: list[ApprovedWorkflow]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are selecting and tailoring a ComfyUI workflow recommendation for an internal engineering team. "
                "Use only the approved workflows provided by the user. "
                "Return valid JSON only with these keys: "
                "stage, workflow_id, workflow_version, recommended_workflow_family, base_model_id, required_nodes, "
                "optional_nodes, model_hints, prompt_template, negative_prompt, reasoning_summary, risk_flags, compatibility_notes, "
                "content_modes_supported, registry_source."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "stage": payload.stage,
                    "expansion_summary": payload.expansion_summary,
                    "prompt_blueprint": payload.prompt_blueprint,
                    "technical_sheet_payload": payload.technical_sheet_payload,
                    "approved_workflows": [workflow.model_dump(mode="json") for workflow in approved_workflows],
                }
            ),
        },
    ]


def _openai_recommendation(payload: CopilotRequest, approved_workflows: list[ApprovedWorkflow]) -> CopilotRecommendation:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY or OPEN_AI_TOKEN is required")
    response_payload = _json_request(
        "POST",
        f"{OPENAI_API_BASE_URL}/chat/completions",
        payload={
            "model": OPENAI_API_MODEL,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": _build_messages(payload, approved_workflows),
        },
        timeout_seconds=COPILOT_TIMEOUT_SECONDS,
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
    )
    parsed = _extract_json_text(response_payload)
    recommendation = CopilotRecommendation.model_validate(parsed)
    approved_by_id = {workflow.workflow_id: workflow for workflow in approved_workflows}
    approved = approved_by_id.get(recommendation.workflow_id)
    if approved is None:
        raise RuntimeError("OpenAI selected a workflow outside the approved registry")
    if recommendation.stage != approved.stage:
        raise RuntimeError("OpenAI returned a stage that does not match the approved workflow")
    return recommendation


app = FastAPI(title="VixenBliss ComfyUI Copilot")


@app.get("/healthcheck")
def healthcheck() -> dict[str, Any]:
    stage_entries = {stage.value: len(workflow_registry.for_stage(stage)) for stage in CopilotStage}
    return {
        "ok": True,
        "service": "comfyui_copilot",
        "provider": "openai",
        "provider_ready": bool(OPENAI_API_KEY),
        "openai_api_model": OPENAI_API_MODEL,
        "default_stage": COPILOT_DEFAULT_STAGE,
        "registry_entries": stage_entries,
    }


@app.post("/recommend")
def recommend(payload: CopilotRequest) -> dict[str, Any]:
    approved_workflows = _recommended_workflows(payload)
    if not approved_workflows:
        raise HTTPException(status_code=422, detail="No approved workflows available for the requested stage")
    try:
        recommendation = _openai_recommendation(payload, approved_workflows)
    except Exception as exc:
        recommendation = _fallback_recommendation(payload, reason=str(exc))
    return recommendation.model_dump(mode="json")


web_app = app
