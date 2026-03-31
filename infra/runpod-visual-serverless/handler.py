from __future__ import annotations

import base64
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
COMFYUI_OUTPUT_DIR = COMFYUI_HOME / "output"
COMFYUI_MODELS_DIR = Path(os.getenv("COMFYUI_MODELS_DIR", str(COMFYUI_HOME / "models")))
COMFYUI_WORKFLOW_IMAGE_ID = os.getenv("COMFYUI_WORKFLOW_IMAGE_ID", "base-image-ipadapter-impact")
COMFYUI_WORKFLOW_IMAGE_VERSION = os.getenv("COMFYUI_WORKFLOW_IMAGE_VERSION", "2026-03-30")
COMFYUI_BASE_CHECKPOINT_NAME = os.getenv("COMFYUI_BASE_CHECKPOINT_NAME", "base-image-model.safetensors")
COMFYUI_IP_ADAPTER_MODEL = os.getenv("COMFYUI_IP_ADAPTER_MODEL", "plus_face")
COMFYUI_FACE_CONFIDENCE_THRESHOLD = float(os.getenv("COMFYUI_FACE_CONFIDENCE_THRESHOLD", "0.8"))

WORKFLOW_TEMPLATE = Path("/opt/runpod-visual-serverless/workflows") / f"{COMFYUI_WORKFLOW_IMAGE_ID}.json"
ENTRYPOINT_SCRIPT = Path("/opt/runpod-visual-serverless/scripts/entrypoint.sh")

_COMFYUI_PROCESS: subprocess.Popen[str] | None = None


def _response_error(code: str, message: str, metadata: dict | None = None) -> dict:
    return {
        "provider": "runpod",
        "workflow_id": COMFYUI_WORKFLOW_IMAGE_ID,
        "workflow_version": COMFYUI_WORKFLOW_IMAGE_VERSION,
        "artifacts": [],
        "error_code": code,
        "error_message": message,
        "metadata": metadata or {},
    }


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


def _assert_required_runtime_inputs(job_input: dict) -> None:
    checkpoint_name = job_input.get("base_checkpoint_name", COMFYUI_BASE_CHECKPOINT_NAME)
    checkpoint_path = COMFYUI_MODELS_DIR / "checkpoints" / checkpoint_name
    if not checkpoint_path.exists():
        raise RuntimeError(f"COMFYUI_EXECUTION_FAILED: missing checkpoint {checkpoint_name}")

    ip_adapter_path = COMFYUI_MODELS_DIR / "ipadapter" / f"{COMFYUI_IP_ADAPTER_MODEL}.safetensors"
    if not ip_adapter_path.exists():
        raise RuntimeError(f"COMFYUI_EXECUTION_FAILED: missing ip adapter model {COMFYUI_IP_ADAPTER_MODEL}.safetensors")


def _download_remote_file(file_url: str, prefix: str) -> str:
    COMFYUI_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(parse.urlparse(file_url).path).suffix or ".png"
    filename = f"{prefix}-{uuid.uuid4().hex}{suffix}"
    target = COMFYUI_INPUT_DIR / filename
    try:
        with requests.get(file_url, timeout=60, stream=True) as response:
            response.raise_for_status()
            with target.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
    except requests.HTTPError as exc:
        raise FileNotFoundError(f"could not download {file_url}: {exc}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"failed downloading {file_url}: {exc}") from exc
    return filename


def _materialize_resume_base_image(job_input: dict) -> str:
    checkpoint = job_input.get("resume_checkpoint") or {}
    artifacts = checkpoint.get("intermediate_artifacts") or []
    for artifact in artifacts:
        if artifact.get("role") != "base_image":
            continue
        metadata = artifact.get("metadata_json") or {}
        inline_data = metadata.get("inline_data_base64")
        if inline_data:
            filename = f"resume-base-{uuid.uuid4().hex}.png"
            target = COMFYUI_INPUT_DIR / filename
            target.write_bytes(base64.b64decode(inline_data))
            return filename
        artifact_uri = artifact.get("uri")
        if artifact_uri:
            return _download_remote_file(artifact_uri, "resume-base")
    raise RuntimeError("RESUME_STATE_INCOMPLETE: resume checkpoint does not include a usable base_image artifact")


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
    mode = job_input.get("mode", "base_render")

    workflow["checkpoint_loader"]["inputs"]["ckpt_name"] = job_input.get("base_checkpoint_name", COMFYUI_BASE_CHECKPOINT_NAME)
    workflow["positive_prompt"]["inputs"]["text"] = positive_prompt
    workflow["negative_prompt"]["inputs"]["text"] = negative_prompt
    workflow["empty_latent"]["inputs"]["width"] = width
    workflow["empty_latent"]["inputs"]["height"] = height
    workflow["load_ip_adapter_model"]["inputs"]["ipadapter_file"] = f"{COMFYUI_IP_ADAPTER_MODEL}.safetensors"
    workflow["ksampler"]["inputs"]["seed"] = seed
    workflow["face_detailer"]["inputs"]["seed"] = seed
    workflow["face_detailer"]["inputs"]["bbox_threshold"] = confidence_threshold
    workflow["face_detailer"]["inputs"]["denoise"] = float(job_input.get("inpaint_strength", workflow["face_detailer"]["inputs"]["denoise"]))

    reference_face_image_url = job_input.get("reference_face_image_url")
    if reference_face_image_url:
        workflow["load_reference_image"]["inputs"]["image"] = _download_remote_file(reference_face_image_url, "reference")
    elif mode != "face_detail":
        fallback_reference = job_input.get("reference_face_image_name")
        if fallback_reference:
            workflow["load_reference_image"]["inputs"]["image"] = fallback_reference
        else:
            raise FileNotFoundError("reference_face_image_url could not be resolved")

    if mode == "base_render":
        workflow.pop("save_final_image", None)
        workflow["vb_meta"]["requested_stage"] = "base_render"
        return workflow

    if mode == "face_detail":
        workflow.pop("save_base_image", None)
        resume_image_name = _materialize_resume_base_image(job_input)
        workflow["resume_base_image"] = {
            "class_type": "LoadImage",
            "inputs": {"image": resume_image_name},
        }
        workflow["face_detailer"]["inputs"]["image"] = ["resume_base_image", 0]
        workflow["vb_meta"]["requested_stage"] = "face_detail"
        workflow["vb_meta"]["resume_checkpoint"] = job_input.get("resume_checkpoint")
        return workflow

    raise RuntimeError(f"COMFYUI_EXECUTION_FAILED: unsupported mode {mode}")


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


def _artifact_path(image: dict) -> Path:
    subfolder = image.get("subfolder", "")
    return COMFYUI_OUTPUT_DIR / subfolder / image["filename"]


def _build_artifact(image: dict, *, role: str, inline_bytes: bool) -> dict:
    artifact = {
        "role": role,
        "uri": str(_artifact_path(image)),
        "content_type": "image/png",
        "metadata_json": {
            "filename": image.get("filename", ""),
            "subfolder": image.get("subfolder", ""),
            "type": image.get("type", "output"),
        },
    }
    query = parse.urlencode(
        {
            "filename": image.get("filename", ""),
            "subfolder": image.get("subfolder", ""),
            "type": image.get("type", "output"),
        }
    )
    if COMFYUI_PUBLIC_BASE_URL:
        artifact["uri"] = f"{COMFYUI_PUBLIC_BASE_URL}/view?{query}"
    path = _artifact_path(image)
    if inline_bytes and path.exists():
        artifact["metadata_json"]["inline_data_base64"] = base64.b64encode(path.read_bytes()).decode("ascii")
    return artifact


def _extract_artifacts(history_payload: dict, *, mode: str) -> list[dict]:
    artifacts: list[dict] = []
    outputs = history_payload.get("outputs", {})
    for output_node_id, output in outputs.items():
        if not isinstance(output, dict):
            continue
        for image in output.get("images", []):
            if not image.get("filename"):
                continue
            if mode == "base_render" and output_node_id == "save_base_image":
                artifacts.append(_build_artifact(image, role="base_image", inline_bytes=True))
            if mode == "face_detail" and output_node_id == "save_final_image":
                artifacts.append(_build_artifact(image, role="final_image", inline_bytes=False))
    return artifacts


def _find_numeric(obj: object, key_names: set[str]) -> float | None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            lowered = key.lower()
            if lowered in key_names and isinstance(value, (int, float)) and 0.0 <= float(value) <= 1.0:
                return float(value)
            found = _find_numeric(value, key_names)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_numeric(item, key_names)
            if found is not None:
                return found
    return None


def _extract_face_confidence(history_payload: dict, job_input: dict) -> float | None:
    override = job_input.get("face_detection_confidence_override")
    if isinstance(override, (int, float)):
        return float(override)
    metadata = history_payload.get("metadata")
    if isinstance(metadata, dict):
        direct = metadata.get("face_detection_confidence")
        if isinstance(direct, (int, float)):
            return float(direct)
    outputs = history_payload.get("outputs", {})
    if "face_detector" in outputs:
        detector_payload = outputs["face_detector"]
        confidence = _find_numeric(detector_payload, {"face_detection_confidence", "confidence", "score", "bbox_confidence"})
        if confidence is not None:
            return confidence
    return _find_numeric(history_payload, {"face_detection_confidence"})


def _run_generation(job_input: dict) -> dict:
    _ensure_comfyui_running()
    _assert_required_runtime_inputs(job_input)

    mode = job_input.get("mode", "base_render")
    workflow = _build_workflow_payload(job_input)
    payload = {
        "client_id": f"runpod-{uuid.uuid4().hex}",
        "prompt": workflow,
        "extra_data": {
            "workflow_id": COMFYUI_WORKFLOW_IMAGE_ID,
            "workflow_version": COMFYUI_WORKFLOW_IMAGE_VERSION,
            "mode": mode,
        },
    }
    response = requests.post(f"{COMFYUI_BASE_URL}/prompt", json=payload, timeout=60)
    response.raise_for_status()
    submission = response.json()
    prompt_id = submission.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI prompt submission did not return prompt_id: {submission}")

    history = _poll_history(prompt_id)
    artifacts = _extract_artifacts(history, mode=mode)
    if not artifacts:
        raise RuntimeError("COMFYUI_EXECUTION_FAILED: ComfyUI execution did not expose any artifacts")

    face_detection_confidence = _extract_face_confidence(history, job_input)
    if mode == "base_render" and face_detection_confidence is None:
        return _response_error(
            "FACE_CONFIDENCE_UNAVAILABLE",
            "face detector did not return a usable confidence score",
            {"prompt_id": prompt_id},
        )

    return {
        "provider": "runpod",
        "workflow_id": COMFYUI_WORKFLOW_IMAGE_ID,
        "workflow_version": COMFYUI_WORKFLOW_IMAGE_VERSION,
        "provider_job_id": prompt_id,
        "prompt_id": prompt_id,
        "artifacts": artifacts,
        "successful_node_ids": list(history.get("outputs", {}).keys()),
        "face_detection_confidence": face_detection_confidence,
        "ip_adapter_used": bool(job_input.get("reference_face_image_url")),
        "regional_inpaint_triggered": mode == "face_detail",
        "metadata": {
            "mode": mode,
            "requested_threshold": job_input.get("face_confidence_threshold", COMFYUI_FACE_CONFIDENCE_THRESHOLD),
            "workflow_id": COMFYUI_WORKFLOW_IMAGE_ID,
            "workflow_version": COMFYUI_WORKFLOW_IMAGE_VERSION,
        },
    }


def handler(job: dict) -> dict:
    job_input = job.get("input", {})
    action = job_input.get("action", "generate")

    try:
        _ensure_comfyui_running()
        if action == "healthcheck":
            checkpoint_name = job_input.get("base_checkpoint_name", COMFYUI_BASE_CHECKPOINT_NAME)
            return {
                "ok": True,
                "provider": "runpod",
                "comfyui_base_url": COMFYUI_BASE_URL,
                "workflow_id": COMFYUI_WORKFLOW_IMAGE_ID,
                "workflow_version": COMFYUI_WORKFLOW_IMAGE_VERSION,
                "ip_adapter_model": COMFYUI_IP_ADAPTER_MODEL,
                "handler_entrypoint": str(ENTRYPOINT_SCRIPT),
                "runtime_checks": {
                    "checkpoint_present": (COMFYUI_MODELS_DIR / "checkpoints" / checkpoint_name).exists(),
                    "ip_adapter_present": (COMFYUI_MODELS_DIR / "ipadapter" / f"{COMFYUI_IP_ADAPTER_MODEL}.safetensors").exists(),
                    "workflow_baked": WORKFLOW_TEMPLATE.exists(),
                },
            }
        if action != "generate":
            return _response_error("COMFYUI_EXECUTION_FAILED", f"unsupported action {action}")
        return _run_generation(job_input)
    except FileNotFoundError as exc:
        return _response_error("REFERENCE_IMAGE_NOT_FOUND", str(exc))
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith("RESUME_STATE_INCOMPLETE:"):
            return _response_error("RESUME_STATE_INCOMPLETE", message.split(":", 1)[1].strip())
        if message.startswith("COMFYUI_EXECUTION_FAILED:"):
            return _response_error("COMFYUI_EXECUTION_FAILED", message.split(":", 1)[1].strip())
        return _response_error("COMFYUI_EXECUTION_FAILED", message)
    except requests.RequestException as exc:
        return _response_error("COMFYUI_EXECUTION_FAILED", f"ComfyUI request failed: {exc}")


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
