from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from vixenbliss_creator.s1_services import GenerationServiceInput, InMemoryServiceRuntime, build_generation_manifest


ARTIFACT_ROOT = Path(os.getenv("SERVICE_ARTIFACT_ROOT", "/tmp/vixenbliss/s1-llm"))
ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)


def _persist_manifest(result: dict) -> dict:
    artifact_path = result["generation_manifest"]["artifact_path"]
    target = ARTIFACT_ROOT / Path(artifact_path).name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    result["generation_manifest"]["artifact_path"] = str(target.as_posix())
    return result


def _processor(payload: dict) -> dict:
    request = GenerationServiceInput.model_validate(payload)
    manifest = build_generation_manifest(request)
    return _persist_manifest(
        {
            "service": "s1_llm",
            "provider": "modal",
            "generation_manifest": manifest.model_dump(mode="json"),
        }
    )


runtime = InMemoryServiceRuntime(processor=_processor)
app = FastAPI(title="VixenBliss S1 LLM Runtime", version="1.0.0")


@app.get("/healthcheck")
def healthcheck() -> dict:
    return {"ok": True, "service": "s1_llm", "provider": "modal", "progress_transport": "websocket_optional"}


@app.post("/jobs")
def submit_job(payload: dict) -> dict:
    record = runtime.submit(payload.get("input", payload))
    return record.status_payload(
        progress_url=f"/ws/jobs/{record.job_id}",
        result_url=f"/jobs/{record.job_id}/result",
    )


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    try:
        record = runtime.status(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    return record.status_payload(
        progress_url=f"/ws/jobs/{record.job_id}",
        result_url=f"/jobs/{record.job_id}/result",
    )


@app.get("/jobs/{job_id}/result")
def get_result(job_id: str) -> dict:
    try:
        return runtime.result(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.websocket("/ws/jobs/{job_id}")
async def stream_job(job_id: str, websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        record = runtime.status(job_id)
    except KeyError:
        await websocket.send_json({"error": "job not found"})
        await websocket.close(code=4404)
        return
    try:
        for event in record.progress_events:
            await websocket.send_json(event.model_dump(mode="json"))
    except WebSocketDisconnect:
        return
    await websocket.close()
