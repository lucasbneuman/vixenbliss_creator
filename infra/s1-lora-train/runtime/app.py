from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from vixenbliss_creator.s1_control import S1ControlSettings, S1RuntimeDirectusRecorder
from vixenbliss_creator.s1_services import InMemoryServiceRuntime, LoraTrainingServiceInput, build_lora_training_result


ARTIFACT_ROOT = Path(os.getenv("SERVICE_ARTIFACT_ROOT", "/tmp/vixenbliss/s1-lora-train"))
ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)


def _persist_training_manifest(result: dict) -> dict:
    manifest = result["training_manifest"]
    manifest_path = ARTIFACT_ROOT / Path(manifest["result_manifest_path"]).name
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    result["training_manifest"]["result_manifest_path"] = manifest_path.as_posix()
    return result


def _processor(payload: dict) -> dict:
    request = LoraTrainingServiceInput.model_validate(
        {
            **payload,
            "artifact_root": payload.get("artifact_root", ARTIFACT_ROOT.as_posix()),
        }
    )
    return _persist_training_manifest(build_lora_training_result(request))


runtime = InMemoryServiceRuntime(processor=_processor)
app = FastAPI(title="VixenBliss S1 LoRA Train Runtime", version="1.0.0")

try:
    _directus_recorder = S1RuntimeDirectusRecorder.from_settings(S1ControlSettings.from_env())
except Exception:
    _directus_recorder = None


@app.get("/healthcheck")
def healthcheck() -> dict:
    return {"ok": True, "service": "s1_lora_train", "provider": "modal", "progress_transport": "websocket_optional"}


@app.post("/jobs")
def submit_job(payload: dict) -> dict:
    job_input = payload.get("input", payload)
    record = runtime.submit(job_input)
    if _directus_recorder is not None:
        try:
            _directus_recorder.record_job(
                service_name="s1_lora_train",
                job_id=record.job_id,
                status=record.status.value,
                input_payload=job_input,
                result_payload=record.result,
                error_message=record.error_message,
            )
        except Exception:
            pass
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
