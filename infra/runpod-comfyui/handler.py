from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from urllib import parse, request

import requests
import runpod


COMFYUI_HOME = Path(os.getenv("COMFYUI_HOME", "/opt/comfyui"))
COMFYUI_PORT = int(os.getenv("COMFYUI_PORT", "8188"))
COMFYUI_LISTEN = os.getenv("COMFYUI_LISTEN", "0.0.0.0")
COMFYUI_BASE_URL = os.getenv("COMFYUI_BASE_URL", f"http://127.0.0.1:{COMFYUI_PORT}").rstrip("/")
COMFYUI_PUBLIC_BASE_URL = os.getenv("COMFYUI_PUBLIC_BASE_URL", "").rstrip("/")
COMFYUI_USER_DIR = Path(os.getenv("COMFYUI_USER_DIR", str(COMFYUI_HOME / "user" / "default")))
COMFYUI_INPUT_DIR = Path(os.getenv("COMFYUI_INPUT_DIR", str(COMFYUI_HOME / "input")))
COMFYUI_WORKFLOW_IMAGE_ID = os.getenv("COMFYUI_WORKFLOW_IMAGE_ID", "base-image-ipadapter-impact")
COMFYUI_WORKFLOW_IMAGE_VERSION = os.getenv("COMFYUI_WORKFLOW_IMAGE_VERSION", "2026-03-30")
COMFYUI_BASE_CHECKPOINT_NAME = os.getenv("COMFYUI_BASE_CHECKPOINT_NAME", "base-image-model.safetensors")
COMFYUI_IP_ADAPTER_MODEL = os.getenv("COMFYUI_IP_ADAPTER_MODEL", "plus_face")
COMFYUI_FACE_CONFIDENCE_THRESHOLD = float(os.getenv("COMFYUI_FACE_CONFIDENCE_THRESHOLD", "0.8"))

WORKFLOW_TEMPLATE = Path("/opt/runpod-comfyui/workflows") / f"{COMFYUI_WORKFLOW_IMAGE_ID}.json"
ENTRYPOINT_SCRIPT = Path("/opt/runpod-comfyui/scripts/entrypoint.sh")

_COMFYUI_PROCESS: subprocess.Popen[str] | None = None


def _copy_workflow() -> None:
    target = COMFYUI_USER_DIR / "workflows" / f"{COMFYUI_WORKFLOW_IMAGE_ID}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(WORKFLOW_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")


def _healthcheck(timeout_seconds: int = 2) -> bool:
    try:
        with request.urlopen(f"{COMFYUI_BASE_URL}/system_stats", timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return isinstance(payload, dict)
    except Exception:
        return False


def _ensure_comfyui_running() -> None:
    global _COMFYUI_PROCESS

    if _healthcheck():
        return

    _copy_workflow()

    if _COMFYUI_PROCESS is None or _COMFYUI_PROCESS.poll() is not None:
        _COMFYUI_PROCESS = subprocess.Popen(
            ["/bin/bash", str(ENTRYPOINT_SCRIPT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

    deadline = time.time() + 120
    while time.time() < deadline:
        if _healthcheck():
            return
        if _COMFYUI_PROCESS and _COMFYUI_PROCESS.poll() is not None:
            output = ""
            if _COMFYUI_PROCESS.stdout is not None:
                output = _COMFYUI_PROCESS.stdout.read()
            raise RuntimeError(f"ComfyUI process exited before becoming healthy. Output: {output}")
        time.sleep(2)
    raise TimeoutError("ComfyUI did not become healthy within the expected startup window")


def _download_reference_image(reference_face_image_url: str) -> str:
    COMFYUI_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(parse.urlparse(reference_face_image_url).path).suffix or ".png"
    filename = f"reference-{uuid.uuid4().hex}{suffix}"
    target = COMFYUI_INPUT_DIR / filename
    with requests.get(reference_face_image_url, timeout=30, stream=True) as response:
        response.raise_for_status()
        with target.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)
    return filename


def _build_workflow_payload(job_input: dict) -> dict:
    workflow = json.loads(WORKFLOW_TEMPLATE.read_text(encoding="utf-8"))
    workflow["workflow_id"] = COMFYUI_WORKFLOW_IMAGE_ID
    workflow["workflow_version"] = COMFYUI_WORKFLOW_IMAGE_VERSION
    workflow["vb_meta"]["workflow_id"] = COMFYUI_WORKFLOW_IMAGE_ID
    workflow["vb_meta"]["workflow_version"] = COMFYUI_WORKFLOW_IMAGE_VERSION

    positive_prompt = job_input.get("prompt", "portrait of a synthetic performer")
    negative_prompt = job_input.get(
        "negative_prompt",
        "low quality, anatomy drift, extra limbs, text, watermark",
    )
    seed = int(job_input.get("seed", 42))
    width = int(job_input.get("width", 1024))
    height = int(job_input.get("height", 1024))
    confidence_threshold = float(job_input.get("face_confidence_threshold", COMFYUI_FACE_CONFIDENCE_THRESHOLD))

    workflow["checkpoint_loader"]["inputs"]["ckpt_name"] = job_input.get(
        "base_checkpoint_name",
        COMFYUI_BASE_CHECKPOINT_NAME,
    )
    workflow["positive_prompt"]["inputs"]["text"] = positive_prompt
    workflow["negative_prompt"]["inputs"]["text"] = negative_prompt
    workflow["empty_latent"]["inputs"]["width"] = width
    workflow["empty_latent"]["inputs"]["height"] = height
    workflow["load_ip_adapter_model"]["inputs"]["ipadapter_file"] = f"{COMFYUI_IP_ADAPTER_MODEL}.safetensors"
    workflow["ksampler"]["inputs"]["seed"] = seed
    workflow["face_detailer"]["inputs"]["seed"] = seed
    workflow["face_detailer"]["inputs"]["bbox_threshold"] = confidence_threshold

    reference_face_image_url = job_input.get("reference_face_image_url")
    if reference_face_image_url:
        workflow["load_reference_image"]["inputs"]["image"] = _download_reference_image(reference_face_image_url)
    else:
        workflow["load_reference_image"]["inputs"]["image"] = job_input.get(
            "reference_face_image_name",
            "CHANGEME_REFERENCE_IMAGE.png",
        )

    return workflow


def _poll_history(prompt_id: str) -> dict:
    deadline = time.time() + 600
    history_url = f"{COMFYUI_BASE_URL}/history/{prompt_id}"
    while time.time() < deadline:
        with request.urlopen(history_url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        result = payload.get(prompt_id, payload)
        if isinstance(result, dict) and result.get("outputs"):
            return result
        time.sleep(2)
    raise TimeoutError(f"ComfyUI history for prompt_id={prompt_id} did not complete in time")


def _extract_artifacts(history_payload: dict) -> list[dict]:
    artifacts: list[dict] = []
    outputs = history_payload.get("outputs", {})
    for output in outputs.values():
        if not isinstance(output, dict):
            continue
        for image in output.get("images", []):
            filename = image.get("filename")
            if not filename:
                continue
            artifact = {
                "filename": filename,
                "subfolder": image.get("subfolder", ""),
                "type": image.get("type", "output"),
            }
            if COMFYUI_PUBLIC_BASE_URL:
                query = parse.urlencode(artifact)
                artifact["public_url"] = f"{COMFYUI_PUBLIC_BASE_URL}/view?{query}"
            artifacts.append(artifact)
    return artifacts


def handler(job: dict) -> dict:
    job_input = job.get("input", {})
    action = job_input.get("action", "generate")

    _ensure_comfyui_running()

    if action == "healthcheck":
        return {
            "ok": True,
            "comfyui_base_url": COMFYUI_BASE_URL,
            "workflow_id": COMFYUI_WORKFLOW_IMAGE_ID,
            "workflow_version": COMFYUI_WORKFLOW_IMAGE_VERSION,
            "ip_adapter_model": COMFYUI_IP_ADAPTER_MODEL,
        }

    workflow = _build_workflow_payload(job_input)
    payload = {
        "client_id": f"runpod-{uuid.uuid4().hex}",
        "prompt": workflow,
        "extra_data": {
            "workflow_id": COMFYUI_WORKFLOW_IMAGE_ID,
            "workflow_version": COMFYUI_WORKFLOW_IMAGE_VERSION,
        },
    }
    response = requests.post(f"{COMFYUI_BASE_URL}/prompt", json=payload, timeout=60)
    response.raise_for_status()
    submission = response.json()
    prompt_id = submission.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI prompt submission did not return prompt_id: {submission}")

    history = _poll_history(prompt_id)
    artifacts = _extract_artifacts(history)
    return {
        "prompt_id": prompt_id,
        "workflow_id": COMFYUI_WORKFLOW_IMAGE_ID,
        "workflow_version": COMFYUI_WORKFLOW_IMAGE_VERSION,
        "artifacts": artifacts,
        "raw_history": history,
    }


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
