from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import subprocess
import time
import uuid
import zipfile
from collections.abc import Callable
from collections import Counter
from pathlib import Path
from typing import TextIO
from urllib import error, parse, request
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from vixenbliss_creator.agentic.models import CompletionStatus, GraphState
from vixenbliss_creator.agentic.runner import run_agentic_brain
from vixenbliss_creator.provider import Provider
from vixenbliss_creator.s1_control import S1ControlSettings, S1RuntimeDirectusRecorder
from vixenbliss_creator.s1_services import (
    DatasetServiceInput,
    GenerationManifest,
    InMemoryServiceRuntime,
    SeedBundle,
    build_dataset_result,
    build_dataset_shot_plan,
)
from vixenbliss_creator.traceability import normalize_trace_source_text
from vixenbliss_creator.visual_pipeline import ResumeCheckpoint, ResumeStage, RuntimeStage, VisualArtifact, VisualArtifactRole


RUNTIME_ROOT = Path(__file__).resolve().parent


def _discover_web_public_root() -> Path:
    override_root = os.getenv("VB_WEB_PUBLIC_ROOT", "").strip()
    if override_root:
        candidate = Path(override_root).expanduser().resolve()
        if (candidate / "index.html").exists():
            return candidate

    for base in (RUNTIME_ROOT, *RUNTIME_ROOT.parents):
        candidate = base / "apps" / "web" / "public"
        if (candidate / "index.html").exists():
            return candidate

    # Coolify/container fallback when the web app is copied alongside the runtime.
    for candidate in (
        Path("/app/apps/web/public"),
        Path("/workspace/apps/web/public"),
    ):
        if (candidate / "index.html").exists():
            return candidate

    raise RuntimeError("web app public root is missing; expected apps/web/public/index.html")


WEB_PUBLIC_ROOT = _discover_web_public_root()
WEB_APP_ROOT = WEB_PUBLIC_ROOT.parent
WEB_ASSETS_ROOT = WEB_PUBLIC_ROOT / "assets"
ARTIFACT_ROOT = Path(os.getenv("SERVICE_ARTIFACT_ROOT", "/tmp/vixenbliss/s1-image"))
COMFYUI_HOME = Path(os.getenv("COMFYUI_HOME", "/opt/comfyui"))
COMFYUI_PORT = int(os.getenv("COMFYUI_PORT", "8188"))
COMFYUI_LISTEN = os.getenv("COMFYUI_LISTEN", "0.0.0.0")
COMFYUI_BASE_URL = os.getenv("COMFYUI_BASE_URL", f"http://127.0.0.1:{COMFYUI_PORT}").rstrip("/")
COMFYUI_PUBLIC_BASE_URL = os.getenv("COMFYUI_PUBLIC_BASE_URL", "").rstrip("/")
COMFYUI_USER_DIR = Path(os.getenv("COMFYUI_USER_DIR", str(COMFYUI_HOME / "user" / "default")))
COMFYUI_INPUT_DIR = Path(os.getenv("COMFYUI_INPUT_DIR", str(COMFYUI_HOME / "input")))
COMFYUI_OUTPUT_DIR = COMFYUI_HOME / "output"
COMFYUI_MODELS_DIR = Path(os.getenv("COMFYUI_MODELS_DIR", str(COMFYUI_HOME / "models")))
COMFYUI_CUSTOM_NODES_DIR = Path(os.getenv("COMFYUI_CUSTOM_NODES_DIR", str(COMFYUI_HOME / "custom_nodes")))
COMFYUI_WORKFLOW_IMAGE_ID = os.getenv(
    "COMFYUI_WORKFLOW_IDENTITY_ID",
    os.getenv("COMFYUI_WORKFLOW_IMAGE_ID", "base-image-ipadapter-impact"),
)
COMFYUI_WORKFLOW_IMAGE_VERSION = os.getenv(
    "COMFYUI_WORKFLOW_IDENTITY_VERSION",
    os.getenv("COMFYUI_WORKFLOW_IMAGE_VERSION", "2026-03-31"),
)
COMFYUI_FLUX_DIFFUSION_MODEL_NAME = os.getenv("COMFYUI_FLUX_DIFFUSION_MODEL_NAME", "flux1-schnell.safetensors")
COMFYUI_FLUX_AE_NAME = os.getenv("COMFYUI_FLUX_AE_NAME", "ae.safetensors")
COMFYUI_FLUX_CLIP_L_NAME = os.getenv("COMFYUI_FLUX_CLIP_L_NAME", "clip_l.safetensors")
COMFYUI_FLUX_T5XXL_NAME = os.getenv("COMFYUI_FLUX_T5XXL_NAME", "t5xxl_fp8_e4m3fn.safetensors")
COMFYUI_FLUX_UNET_WEIGHT_DTYPE = os.getenv("COMFYUI_FLUX_UNET_WEIGHT_DTYPE", "default")
COMFYUI_IP_ADAPTER_MODEL = os.getenv("COMFYUI_IP_ADAPTER_MODEL", "plus_face")
COMFYUI_IP_ADAPTER_CLIP_VISION_MODEL = os.getenv(
    "COMFYUI_IP_ADAPTER_CLIP_VISION_MODEL",
    "google/siglip-so400m-patch14-384",
)
COMFYUI_IP_ADAPTER_CLIP_VISION_DIRNAME = COMFYUI_IP_ADAPTER_CLIP_VISION_MODEL.split("/")[-1]
COMFYUI_FACE_DETECTOR_MODEL = os.getenv("COMFYUI_FACE_DETECTOR_MODEL", "face_yolov8m.pt")
COMFYUI_FACE_CONFIDENCE_THRESHOLD = float(os.getenv("COMFYUI_FACE_CONFIDENCE_THRESHOLD", "0.8"))
MODEL_CACHE_ROOT = Path(
    os.getenv(
        "MODEL_CACHE_ROOT",
        os.getenv("RUNPOD_MODELS_ROOT", os.getenv("RUNPOD_VOLUME_PATH", "/cache/models")),
    )
)
MODEL_BOOTSTRAP_WAIT_SECONDS = int(os.getenv("MODEL_BOOTSTRAP_WAIT_SECONDS", "45"))
COMFYUI_HISTORY_TIMEOUT_SECONDS = int(os.getenv("COMFYUI_HISTORY_TIMEOUT_SECONDS", "1800"))
WORKFLOW_TEMPLATE_DIR = RUNTIME_ROOT / "workflows"
DEFAULT_WORKFLOW_TEMPLATE = WORKFLOW_TEMPLATE_DIR / f"{COMFYUI_WORKFLOW_IMAGE_ID}.json"
ENTRYPOINT_SCRIPT = RUNTIME_ROOT / "scripts" / "entrypoint.sh"
S1_IMAGE_EXECUTION_BACKEND = os.getenv("S1_IMAGE_EXECUTION_BACKEND", "local").strip().lower()
S1_IMAGE_MODAL_APP_NAME = os.getenv("S1_IMAGE_MODAL_APP_NAME", "vixenbliss-s1-image")
S1_IMAGE_MODAL_FUNCTION_NAME = os.getenv("S1_IMAGE_MODAL_FUNCTION_NAME", "run_s1_image_job")
S1_IMAGE_MODAL_HEALTHCHECK_FUNCTION_NAME = os.getenv("S1_IMAGE_MODAL_HEALTHCHECK_FUNCTION_NAME", "runtime_healthcheck")
LAB_DEFAULT_REFERENCE_FACE_IMAGE_URL = os.getenv("LAB_REFERENCE_FACE_IMAGE_URL", "")
WEB_SESSION_COOKIE_NAME = os.getenv("VB_WEB_SESSION_COOKIE_NAME", "vb_web_auth")
WEB_SESSION_TTL_SECONDS = int(os.getenv("VB_WEB_SESSION_TTL_SECONDS", "43200"))
WEB_SESSION_SECRET = os.getenv("VB_WEB_SESSION_SECRET", "vb-web-dev-secret")
WEB_SESSION_SECURE = os.getenv("VB_WEB_SESSION_SECURE", "false").strip().lower() in {"1", "true", "yes", "on"}
LAB_REFERENCE_UPLOAD_ROOT = ARTIFACT_ROOT / "lab-reference-uploads"

ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
LAB_REFERENCE_UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
_COMFYUI_PROCESS: subprocess.Popen[str] | None = None
_COMFYUI_LOG_HANDLE: TextIO | None = None
COMFYUI_LOG_PATH = ARTIFACT_ROOT / "comfyui.log"
_LAB_SESSIONS: dict[str, dict[str, object]] = {}
_LAB_REFERENCE_UPLOADS: dict[str, dict[str, str]] = {}
_WEB_AUTH_SESSIONS: dict[str, dict[str, object]] = {}

ProgressEmitter = Callable[[str, str, float], None]


def _resolved_workflow_id(job_input: dict | None = None) -> str:
    job_input = job_input or {}
    return str(job_input.get("workflow_id", COMFYUI_WORKFLOW_IMAGE_ID))


def _resolved_workflow_version(job_input: dict | None = None) -> str:
    job_input = job_input or {}
    return str(job_input.get("workflow_version", COMFYUI_WORKFLOW_IMAGE_VERSION))


def _workflow_template_path(job_input: dict | None = None) -> Path:
    return WORKFLOW_TEMPLATE_DIR / f"{_resolved_workflow_id(job_input)}.json"


def _resolve_ip_adapter_model_name(job_input: dict | None = None) -> str:
    job_input = job_input or {}
    ip_adapter = job_input.get("ip_adapter") or {}
    requested = str(ip_adapter.get("model_name") or job_input.get("ip_adapter_model_name") or COMFYUI_IP_ADAPTER_MODEL)
    if requested == "plus_face":
        return "ip-adapter.bin"
    return requested


def _response_error(code: str, message: str, metadata: dict | None = None, *, job_input: dict | None = None) -> dict:
    return {
        "provider": Provider.MODAL.value,
        "workflow_id": _resolved_workflow_id(job_input),
        "workflow_version": _resolved_workflow_version(job_input),
        "runtime_stage": RuntimeStage.IDENTITY_IMAGE.value,
        "service_runtime": "s1_image",
        "artifacts": [],
        "error_code": code,
        "error_message": message,
        "metadata": metadata or {},
    }


def _assert_s1_runtime_contract(job_input: dict) -> None:
    runtime_stage = str(job_input.get("runtime_stage") or RuntimeStage.IDENTITY_IMAGE.value)
    if runtime_stage != RuntimeStage.IDENTITY_IMAGE.value:
        raise RuntimeError(f"COMFYUI_EXECUTION_FAILED: unsupported runtime_stage {runtime_stage} for S1 image runtime")
    if job_input.get("lora_version") not in {None, ""}:
        raise RuntimeError("COMFYUI_EXECUTION_FAILED: S1 image runtime must not consume a LoRA version")


def _copy_workflow(job_input: dict | None = None) -> None:
    workflow_template = _workflow_template_path(job_input)
    if not workflow_template.exists():
        raise RuntimeError(
            f"COMFYUI_EXECUTION_FAILED: workflow template {_resolved_workflow_id(job_input)} is not available in the runtime"
        )
    target = COMFYUI_USER_DIR / "workflows" / workflow_template.name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(workflow_template.read_text(encoding="utf-8"), encoding="utf-8")


def _urlopen_json(req: request.Request | str, *, timeout: int) -> dict:
    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace").strip()
        log_tail = _read_recent_comfyui_log()
        log_suffix = f"\n\nComfyUI log tail:\n{log_tail}" if log_tail else ""
        if body:
            raise RuntimeError(f"HTTP {exc.code} from {exc.url}: {body}{log_suffix}") from exc
        raise RuntimeError(f"HTTP {exc.code} from {exc.url}: {exc.reason}{log_suffix}") from exc
    return {} if not raw else json.loads(raw)


def _json_post(url: str, payload: dict, *, timeout: int) -> dict:
    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    return _urlopen_json(req, timeout=timeout)


def _healthcheck(timeout_seconds: int = 2) -> bool:
    try:
        payload = _urlopen_json(f"{COMFYUI_BASE_URL}/system_stats", timeout=timeout_seconds)
    except Exception:
        return False
    return isinstance(payload, dict)


def _emit_progress(emit_progress: ProgressEmitter | None, *, stage: str, message: str, progress: float) -> None:
    if emit_progress is not None:
        emit_progress(stage, message, progress)


def _ensure_comfyui_running(
    *,
    emit_progress: ProgressEmitter | None = None,
    job_input: dict | None = None,
) -> None:
    global _COMFYUI_PROCESS, _COMFYUI_LOG_HANDLE
    if _healthcheck():
        _emit_progress(emit_progress, stage="comfyui_ready", message="ComfyUI already responding", progress=0.26)
        return

    _emit_progress(emit_progress, stage="starting_comfyui", message="Starting embedded ComfyUI runtime", progress=0.18)
    _copy_workflow(job_input)

    if _COMFYUI_PROCESS is None or _COMFYUI_PROCESS.poll() is not None:
        COMFYUI_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if _COMFYUI_LOG_HANDLE is not None:
            _COMFYUI_LOG_HANDLE.close()
        _COMFYUI_LOG_HANDLE = COMFYUI_LOG_PATH.open("a", encoding="utf-8")
        _COMFYUI_LOG_HANDLE.write("\n=== starting comfyui runtime ===\n")
        _COMFYUI_LOG_HANDLE.flush()
        _COMFYUI_PROCESS = subprocess.Popen(
            ["/bin/bash", str(ENTRYPOINT_SCRIPT)],
            stdout=_COMFYUI_LOG_HANDLE,
            stderr=subprocess.STDOUT,
            text=True,
        )

    deadline = time.time() + 120
    while time.time() < deadline:
        if _healthcheck():
            _emit_progress(emit_progress, stage="comfyui_ready", message="ComfyUI became healthy", progress=0.26)
            return
        if _COMFYUI_PROCESS and _COMFYUI_PROCESS.poll() is not None:
            output = _read_recent_comfyui_log()
            raise RuntimeError(f"ComfyUI process exited before becoming healthy. Output: {output}")
        time.sleep(2)
    raise TimeoutError("ComfyUI did not become healthy within the expected startup window")


def _read_recent_comfyui_log(*, max_lines: int = 120) -> str:
    if not COMFYUI_LOG_PATH.exists():
        return ""
    try:
        lines = COMFYUI_LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-max_lines:]).strip()


def _job_requires_reference_assets(job_input: dict | None = None) -> bool:
    job_input = job_input or {}
    ip_adapter = job_input.get("ip_adapter") or {}
    if ip_adapter.get("enabled") is False:
        return False
    return bool(job_input.get("reference_face_image_url") or job_input.get("reference_face_image_name"))


def _required_runtime_paths(job_input: dict | None = None) -> dict[str, Path]:
    job_input = job_input or {}
    paths = {
        "flux_diffusion_model": COMFYUI_MODELS_DIR
        / "diffusion_models"
        / str(job_input.get("flux_diffusion_model_name", COMFYUI_FLUX_DIFFUSION_MODEL_NAME)),
        "flux_ae": COMFYUI_MODELS_DIR / "vae" / str(job_input.get("flux_ae_name", COMFYUI_FLUX_AE_NAME)),
        "flux_clip_l": COMFYUI_MODELS_DIR
        / "text_encoders"
        / str(job_input.get("flux_clip_l_name", COMFYUI_FLUX_CLIP_L_NAME)),
        "flux_t5xxl": COMFYUI_MODELS_DIR
        / "text_encoders"
        / str(job_input.get("flux_t5xxl_name", COMFYUI_FLUX_T5XXL_NAME)),
        "face_detector": COMFYUI_MODELS_DIR / "ultralytics" / "bbox" / str(
            job_input.get("face_detector_model_name", COMFYUI_FACE_DETECTOR_MODEL)
        ),
    }
    if _job_requires_reference_assets(job_input):
        paths["ip_adapter_flux"] = COMFYUI_MODELS_DIR / "ipadapter-flux" / _resolve_ip_adapter_model_name(job_input)
    return paths


def _cache_runtime_paths(job_input: dict | None = None) -> dict[str, Path]:
    job_input = job_input or {}
    paths = {
        "flux_diffusion_model": MODEL_CACHE_ROOT
        / "diffusion_models"
        / str(job_input.get("flux_diffusion_model_name", COMFYUI_FLUX_DIFFUSION_MODEL_NAME)),
        "flux_ae": MODEL_CACHE_ROOT / "vae" / str(job_input.get("flux_ae_name", COMFYUI_FLUX_AE_NAME)),
        "flux_clip_l": MODEL_CACHE_ROOT / "text_encoders" / str(job_input.get("flux_clip_l_name", COMFYUI_FLUX_CLIP_L_NAME)),
        "flux_t5xxl": MODEL_CACHE_ROOT / "text_encoders" / str(job_input.get("flux_t5xxl_name", COMFYUI_FLUX_T5XXL_NAME)),
        "face_detector": MODEL_CACHE_ROOT / "ultralytics" / "bbox" / str(
            job_input.get("face_detector_model_name", COMFYUI_FACE_DETECTOR_MODEL)
        ),
    }
    if _job_requires_reference_assets(job_input):
        paths["ip_adapter_flux"] = MODEL_CACHE_ROOT / "ipadapter-flux" / _resolve_ip_adapter_model_name(job_input)
    return paths


def _clip_vision_runtime_path() -> Path:
    return COMFYUI_MODELS_DIR / "clip_vision" / COMFYUI_IP_ADAPTER_CLIP_VISION_DIRNAME


def _clip_vision_cache_path() -> Path:
    return MODEL_CACHE_ROOT / "clip_vision" / COMFYUI_IP_ADAPTER_CLIP_VISION_DIRNAME


def _runtime_checks(job_input: dict | None = None) -> dict[str, bool]:
    paths = _required_runtime_paths(job_input)
    cache_paths = _cache_runtime_paths(job_input)
    requires_reference_assets = _job_requires_reference_assets(job_input)
    return {
        "flux_diffusion_model_present": paths["flux_diffusion_model"].exists(),
        "flux_ae_present": paths["flux_ae"].exists(),
        "flux_clip_l_present": paths["flux_clip_l"].exists(),
        "flux_t5xxl_present": paths["flux_t5xxl"].exists(),
        "ip_adapter_present": paths["ip_adapter_flux"].exists() if requires_reference_assets else True,
        "cache_flux_diffusion_model_present": cache_paths["flux_diffusion_model"].exists(),
        "cache_flux_ae_present": cache_paths["flux_ae"].exists(),
        "cache_flux_clip_l_present": cache_paths["flux_clip_l"].exists(),
        "cache_flux_t5xxl_present": cache_paths["flux_t5xxl"].exists(),
        "cache_ip_adapter_present": cache_paths["ip_adapter_flux"].exists() if requires_reference_assets else True,
        "face_detector_present": paths["face_detector"].exists(),
        "cache_face_detector_present": cache_paths["face_detector"].exists(),
        "workflow_baked": _workflow_template_path(job_input).exists(),
        "clip_vision_present": _clip_vision_runtime_path().exists() if requires_reference_assets else True,
        "clip_vision_cache_present": _clip_vision_cache_path().exists() if requires_reference_assets else True,
        "comfyui_baked": (COMFYUI_HOME / "main.py").exists(),
        "impact_pack_baked": (COMFYUI_CUSTOM_NODES_DIR / "ComfyUI-Impact-Pack").exists(),
        "impact_subpack_baked": (COMFYUI_CUSTOM_NODES_DIR / "ComfyUI-Impact-Subpack").exists(),
        "ipadapter_flux_baked": (COMFYUI_CUSTOM_NODES_DIR / "ComfyUI-IPAdapter-Flux").exists() if requires_reference_assets else True,
    }


def _runtime_assets_ready(runtime_checks: dict[str, bool], *, allow_cache_only: bool) -> bool:
    file_checks = (
        ("flux_diffusion_model_present", "cache_flux_diffusion_model_present"),
        ("flux_ae_present", "cache_flux_ae_present"),
        ("flux_clip_l_present", "cache_flux_clip_l_present"),
        ("flux_t5xxl_present", "cache_flux_t5xxl_present"),
        ("ip_adapter_present", "cache_ip_adapter_present"),
        ("face_detector_present", "cache_face_detector_present"),
        ("clip_vision_present", "clip_vision_cache_present"),
    )
    for runtime_key, cache_key in file_checks:
        if runtime_checks.get(runtime_key):
            continue
        if allow_cache_only and runtime_checks.get(cache_key):
            continue
        return False
    return all(
        runtime_checks.get(key, False)
        for key in (
            "workflow_baked",
            "comfyui_baked",
            "impact_pack_baked",
            "impact_subpack_baked",
            "ipadapter_flux_baked",
        )
    )


def _assert_required_runtime_inputs(job_input: dict) -> None:
    missing = [(key, path.name) for key, path in _required_runtime_paths(job_input).items() if not path.exists()]
    if missing:
        key, filename = missing[0]
        raise RuntimeError(f"COMFYUI_EXECUTION_FAILED: missing {key} asset {filename}")


def _download_remote_file(file_url: str, prefix: str) -> str:
    COMFYUI_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(parse.urlparse(file_url).path).suffix or ".png"
    filename = f"{prefix}-{uuid.uuid4().hex}{suffix}"
    target = COMFYUI_INPUT_DIR / filename
    try:
        with request.urlopen(file_url, timeout=60) as response:
            target.write_bytes(response.read())
    except error.HTTPError as exc:
        raise FileNotFoundError(f"could not download {file_url}: {exc}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"failed downloading {file_url}: {exc.reason}") from exc
    return filename


def _materialize_resume_base_image(job_input: dict) -> str:
    checkpoint = job_input.get("resume_checkpoint") or {}
    artifacts = checkpoint.get("intermediate_artifacts") or []
    COMFYUI_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    for artifact in artifacts:
        if artifact.get("role") != VisualArtifactRole.BASE_IMAGE.value:
            continue
        metadata = artifact.get("metadata_json") or {}
        inline_data = metadata.get("inline_data_base64")
        if inline_data:
            filename = f"resume-base-{uuid.uuid4().hex}.png"
            (COMFYUI_INPUT_DIR / filename).write_bytes(base64.b64decode(inline_data))
            return filename
        artifact_uri = artifact.get("uri")
        if artifact_uri:
            return _download_remote_file(artifact_uri, "resume-base")
    raise RuntimeError("RESUME_STATE_INCOMPLETE: resume checkpoint does not include a usable base_image artifact")


def _build_workflow_payload(job_input: dict) -> dict:
    workflow_template = _workflow_template_path(job_input)
    if not workflow_template.exists():
        raise RuntimeError(
            f"COMFYUI_EXECUTION_FAILED: workflow template {_resolved_workflow_id(job_input)} is not available in the runtime"
        )
    workflow = json.loads(workflow_template.read_text(encoding="utf-8"))
    workflow = {
        key: value
        for key, value in workflow.items()
        if isinstance(value, dict) and "class_type" in value and "inputs" in value
    }

    positive_prompt = job_input.get("prompt", "portrait of a synthetic performer")
    negative_prompt = job_input.get("negative_prompt", "low quality, anatomy drift, extra limbs, text, watermark")
    seed = int(job_input.get("seed", 42))
    width = int(job_input.get("width", 1024))
    height = int(job_input.get("height", 1024))
    mode = str(job_input.get("mode", ResumeStage.BASE_RENDER.value))
    ip_adapter = job_input.get("ip_adapter") or {}
    face_detailer = job_input.get("face_detailer") or {}
    confidence_threshold = float(
        job_input.get("face_confidence_threshold", face_detailer.get("confidence_threshold", COMFYUI_FACE_CONFIDENCE_THRESHOLD))
    )
    ip_adapter_weight = float(job_input.get("ip_adapter_weight", ip_adapter.get("weight", 0.85)))

    workflow["load_diffusion_model"]["inputs"]["unet_name"] = job_input.get(
        "flux_diffusion_model_name",
        COMFYUI_FLUX_DIFFUSION_MODEL_NAME,
    )
    workflow["load_diffusion_model"]["inputs"]["weight_dtype"] = job_input.get(
        "flux_unet_weight_dtype",
        COMFYUI_FLUX_UNET_WEIGHT_DTYPE,
    )
    workflow["load_dual_clip"]["inputs"]["clip_name1"] = job_input.get("flux_clip_l_name", COMFYUI_FLUX_CLIP_L_NAME)
    workflow["load_dual_clip"]["inputs"]["clip_name2"] = job_input.get("flux_t5xxl_name", COMFYUI_FLUX_T5XXL_NAME)
    workflow["load_ae"]["inputs"]["vae_name"] = job_input.get("flux_ae_name", COMFYUI_FLUX_AE_NAME)
    workflow["positive_prompt"]["inputs"]["clip_l"] = positive_prompt
    workflow["positive_prompt"]["inputs"]["t5xxl"] = positive_prompt
    workflow["negative_prompt"]["inputs"]["clip_l"] = negative_prompt
    workflow["negative_prompt"]["inputs"]["t5xxl"] = negative_prompt
    workflow["empty_latent"]["inputs"]["width"] = width
    workflow["empty_latent"]["inputs"]["height"] = height
    workflow["model_sampling_flux"]["inputs"]["width"] = width
    workflow["model_sampling_flux"]["inputs"]["height"] = height
    workflow["random_noise"]["inputs"]["noise_seed"] = seed
    workflow["load_ip_adapter_model"]["inputs"]["ipadapter"] = job_input.get(
        "ip_adapter_model_name",
        _resolve_ip_adapter_model_name(job_input),
    )
    workflow["load_ip_adapter_model"]["inputs"]["clip_vision"] = job_input.get(
        "ip_adapter_clip_vision_model",
        COMFYUI_IP_ADAPTER_CLIP_VISION_MODEL,
    )
    workflow["ip_adapter_apply"]["inputs"]["weight"] = ip_adapter_weight
    workflow["sampler_scheduler"]["inputs"]["steps"] = int(job_input.get("steps", 12))
    workflow["ksampler_select"]["inputs"]["sampler_name"] = job_input.get("sampler_name", "euler")
    workflow["face_detailer"]["inputs"]["seed"] = seed
    workflow["face_detailer"]["inputs"]["bbox_threshold"] = confidence_threshold
    workflow["face_detailer"]["inputs"]["steps"] = int(job_input.get("face_detail_steps", 12))
    workflow["face_detailer"]["inputs"]["sampler_name"] = job_input.get("sampler_name", "euler")
    workflow["face_detailer"]["inputs"]["denoise"] = float(
        job_input.get("inpaint_strength", face_detailer.get("inpaint_strength", workflow["face_detailer"]["inputs"]["denoise"]))
    )

    reference_face_image_url = job_input.get("reference_face_image_url")
    if reference_face_image_url:
        workflow["load_reference_image"]["inputs"]["image"] = _download_remote_file(reference_face_image_url, "reference")
    elif mode != ResumeStage.FACE_DETAIL.value:
        fallback_reference = job_input.get("reference_face_image_name")
        if fallback_reference:
            workflow["load_reference_image"]["inputs"]["image"] = fallback_reference
    else:
        fallback_reference = None

    if not reference_face_image_url and not fallback_reference:
        # Allow S1 Image to render without a facial reference by bypassing IP-Adapter nodes.
        for node_name in ("sampler_scheduler", "basic_guider", "face_detailer"):
            workflow[node_name]["inputs"]["model"] = ["model_sampling_flux", 0]

    if mode == ResumeStage.BASE_RENDER.value:
        workflow.pop("save_final_image", None)
        return workflow

    if mode == ResumeStage.FACE_DETAIL.value:
        workflow.pop("save_base_image", None)
        resume_image_name = _materialize_resume_base_image(job_input)
        workflow["resume_base_image"] = {"class_type": "LoadImage", "inputs": {"image": resume_image_name}}
        workflow["face_detailer"]["inputs"]["image"] = ["resume_base_image", 0]
        return workflow

    raise RuntimeError(f"COMFYUI_EXECUTION_FAILED: unsupported mode {mode}")


def _submit_prompt(workflow: dict, *, mode: str, job_input: dict | None = None) -> str:
    payload = {
        "client_id": f"modal-{uuid.uuid4().hex}",
        "prompt": workflow,
        "extra_data": {
            "workflow_id": _resolved_workflow_id(job_input),
            "workflow_version": _resolved_workflow_version(job_input),
            "mode": mode,
        },
    }
    submission = _json_post(f"{COMFYUI_BASE_URL}/prompt", payload, timeout=60)
    prompt_id = submission.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI prompt submission did not return prompt_id: {submission}")
    return str(prompt_id)


def _poll_history(prompt_id: str) -> dict:
    deadline = time.time() + COMFYUI_HISTORY_TIMEOUT_SECONDS
    history_url = f"{COMFYUI_BASE_URL}/history/{prompt_id}"
    while time.time() < deadline:
        payload = _urlopen_json(history_url, timeout=30)
        result = payload.get(prompt_id, payload)
        if isinstance(result, dict) and result.get("outputs"):
            return result
        time.sleep(2)
    log_tail = _read_recent_comfyui_log()
    suffix = f"\n\nComfyUI log tail:\n{log_tail}" if log_tail else ""
    raise TimeoutError(
        f"ComfyUI history for prompt_id={prompt_id} did not complete within {COMFYUI_HISTORY_TIMEOUT_SECONDS}s{suffix}"
    )


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
            if mode == ResumeStage.BASE_RENDER.value and output_node_id == "save_base_image":
                artifacts.append(_build_artifact(image, role=VisualArtifactRole.BASE_IMAGE.value, inline_bytes=True))
            if mode == ResumeStage.FACE_DETAIL.value and output_node_id == "save_final_image":
                artifacts.append(_build_artifact(image, role=VisualArtifactRole.FINAL_IMAGE.value, inline_bytes=False))
    return artifacts


def _find_numeric(obj: object, key_names: set[str]) -> float | None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in key_names and isinstance(value, (int, float)) and 0.0 <= float(value) <= 1.0:
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
        confidence = _find_numeric(outputs["face_detector"], {"face_detection_confidence", "confidence", "score", "bbox_confidence"})
        if confidence is not None:
            return confidence
    return _find_numeric(history_payload, {"face_detection_confidence"})


def _build_resume_checkpoint(*, job_input: dict, artifacts: list[dict], prompt_id: str, successful_node_ids: list[str], stage: ResumeStage, face_detection_confidence: float | None) -> dict:
    validated_artifacts = [VisualArtifact.model_validate(item) for item in artifacts]
    checkpoint = ResumeCheckpoint(
        workflow_id=str(job_input.get("workflow_id", COMFYUI_WORKFLOW_IMAGE_ID)),
        workflow_version=str(job_input.get("workflow_version", COMFYUI_WORKFLOW_IMAGE_VERSION)),
        base_model_id=str(job_input.get("base_model_id", "flux-schnell-v1")),
        seed=int(job_input.get("seed", 42)),
        stage=stage,
        provider=Provider.MODAL,
        provider_job_id=prompt_id if stage != ResumeStage.COMPLETED else None,
        successful_node_ids=successful_node_ids,
        intermediate_artifacts=validated_artifacts,
        metadata_json={"face_detection_confidence": face_detection_confidence} if face_detection_confidence is not None else {},
    )
    return checkpoint.model_dump(mode="json")


def _resolve_identity_id(job_input: dict) -> UUID | None:
    metadata = job_input.get("metadata") or {}
    raw = job_input.get("identity_id")
    if raw is None:
        raw = metadata.get("identity_id")
    if raw is None:
        raw = job_input.get("character_id")
    if raw is None:
        raw = metadata.get("character_id")
    if raw in {None, ""}:
        return None
    try:
        return UUID(str(raw))
    except (ValueError, TypeError):
        return None


def _resolve_character_id(job_input: dict) -> str | None:
    metadata = job_input.get("metadata") or {}
    for candidate in (
        job_input.get("character_id"),
        metadata.get("character_id"),
        job_input.get("identity_id"),
        metadata.get("identity_id"),
    ):
        if candidate not in {None, ""}:
            return str(candidate)
    return None


def _resolve_base_image_bytes(artifacts: list[dict]) -> bytes | None:
    for artifact in artifacts:
        if artifact.get("role") != VisualArtifactRole.BASE_IMAGE.value:
            continue
        metadata = artifact.get("metadata_json") or {}
        inline_data = metadata.get("inline_data_base64")
        if inline_data:
            return base64.b64decode(inline_data)
        artifact_uri = artifact.get("uri")
        if artifact_uri and Path(artifact_uri).exists():
            return Path(artifact_uri).read_bytes()
    return None


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _materialize_input_image(image_bytes: bytes, *, prefix: str) -> str:
    COMFYUI_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}-{uuid.uuid4().hex}.png"
    (COMFYUI_INPUT_DIR / filename).write_bytes(image_bytes)
    return filename


def _resolve_artifact_bytes(artifact: dict) -> bytes:
    metadata = artifact.get("metadata_json") or {}
    inline_data = metadata.get("inline_data_base64")
    if inline_data:
        return base64.b64decode(inline_data)
    artifact_uri = artifact.get("uri")
    if artifact_uri and Path(artifact_uri).exists():
        return Path(artifact_uri).read_bytes()
    raise RuntimeError("COMFYUI_EXECUTION_FAILED: generated dataset sample is not materializable")


def _seed_bundle_from_job_input(job_input: dict) -> SeedBundle:
    metadata = job_input.get("metadata") or {}
    explicit_seed_bundle = job_input.get("seed_bundle")
    if not isinstance(explicit_seed_bundle, dict):
        explicit_seed_bundle = metadata.get("seed_bundle") if isinstance(metadata.get("seed_bundle"), dict) else {}
    portrait_seed = int(
        explicit_seed_bundle.get("portrait_seed", job_input.get("seed", metadata.get("portrait_seed", 42)))
    )
    return SeedBundle(
        portrait_seed=portrait_seed,
        variation_seed=int(
            explicit_seed_bundle.get(
                "variation_seed",
                job_input.get("variation_seed", metadata.get("variation_seed", portrait_seed)),
            )
        ),
        dataset_seed=int(
            explicit_seed_bundle.get(
                "dataset_seed",
                job_input.get("dataset_seed", metadata.get("dataset_seed", portrait_seed)),
            )
        ),
    )


def _generate_dataset_samples(
    *,
    job_input: dict,
    dataset_manifest: dict,
    base_image_bytes: bytes,
    emit_progress: ProgressEmitter | None = None,
) -> list[dict]:
    files = dataset_manifest.get("render_files") or dataset_manifest.get("files") or []
    if not files:
        raise RuntimeError("COMFYUI_EXECUTION_FAILED: dataset manifest does not contain any files to render")

    reference_image_name = _materialize_input_image(base_image_bytes, prefix="dataset-reference")
    samples: list[dict] = []
    total = len(files)
    for index, file_entry in enumerate(files, start=1):
        progress = 0.94 + ((index - 1) / max(total, 1)) * 0.04
        _emit_progress(
            emit_progress,
            stage="rendering_dataset_sample",
            message=f"Rendering dataset sample {index}/{total}",
            progress=min(progress, 0.98),
        )
        sample_job_input = dict(job_input)
        sample_job_input.update(
            {
                "prompt": file_entry["prompt"],
                "negative_prompt": file_entry["negative_prompt"],
                "seed": int(file_entry["seed"]),
                "workflow_id": str(dataset_manifest.get("workflow_id") or _resolved_workflow_id(job_input)),
                "workflow_version": str(dataset_manifest.get("workflow_version") or _resolved_workflow_version(job_input)),
                "mode": ResumeStage.BASE_RENDER.value,
                "reference_face_image_url": None,
                "reference_face_image_name": reference_image_name,
                "metadata": {
                    **(job_input.get("metadata") or {}),
                    "dataset_sample_id": file_entry["sample_id"],
                    "dataset_shot_index": index,
                    "dataset_render": True,
                },
            }
        )
        workflow = _build_workflow_payload(sample_job_input)
        prompt_id = _submit_prompt(workflow, mode=ResumeStage.BASE_RENDER.value)
        history = _poll_history(prompt_id)
        artifacts = _extract_artifacts(history, mode=ResumeStage.BASE_RENDER.value)
        if not artifacts:
            raise RuntimeError(
                f"COMFYUI_EXECUTION_FAILED: dataset sample {file_entry['sample_id']} did not expose any render artifacts"
            )
        sample_artifact = artifacts[0]
        sample_bytes = _resolve_artifact_bytes(sample_artifact)
        samples.append(
            {
                "sample_id": file_entry["sample_id"],
                "path": file_entry["path"],
                "framing": file_entry.get("framing"),
                "wardrobe_state": file_entry.get("wardrobe_state"),
                "camera_angle": file_entry.get("camera_angle"),
                "quality_priority": file_entry.get("quality_priority"),
                "bytes": sample_bytes,
                "checksum_sha256": _sha256_bytes(sample_bytes),
                "byte_size": len(sample_bytes),
                "provider_job_id": prompt_id,
                "source_uri": sample_artifact.get("uri"),
            }
        )
    return samples


def _classify_dataset_samples(dataset_manifest: dict) -> dict[str, int]:
    counts = {"SFW": 0, "NSFW": 0}
    for entry in dataset_manifest.get("files", []):
        class_name = str(entry.get("class_name") or "")
        if class_name in counts:
            counts[class_name] += 1
    return counts


def _selection_score(file_entry: dict, sample_data: dict, duplicate_counts: Counter[str]) -> int:
    framing = str(file_entry.get("framing") or "")
    angle = str(file_entry.get("camera_angle") or "")
    quality_priority = str(file_entry.get("quality_priority") or "standard")
    score = {"hero": 300, "standard": 220, "coverage": 140}.get(quality_priority, 180)
    score += {"full_body": 90, "medium": 55, "close_up_face": 40}.get(framing, 0)
    score += {"front": 35, "left_three_quarter": 35, "right_three_quarter": 35, "left_profile": 15, "right_profile": 15}.get(angle, 0)
    score += min(int(sample_data.get("byte_size") or 0) // 32, 40)
    if duplicate_counts[sample_data["checksum_sha256"]] > 1:
        score -= 500
    return score


def _curate_training_subset(dataset_manifest: dict, dataset_samples: list[dict]) -> tuple[list[dict], list[str], dict[str, str], bool]:
    render_files = list(dataset_manifest.get("render_files") or [])
    if not render_files:
        raise RuntimeError("COMFYUI_EXECUTION_FAILED: render_files are required for curated dataset selection")
    target = int(dataset_manifest.get("selected_sample_count") or dataset_manifest.get("sample_count") or 40)
    sample_by_path = {sample["path"]: sample for sample in dataset_samples}
    duplicate_counts = Counter(sample["checksum_sha256"] for sample in dataset_samples)
    selection_reasons: dict[str, str] = dict(dataset_manifest.get("selection_reasons") or {})
    selected_files = [dict(entry) for entry in list(dataset_manifest.get("files") or [])[:target]]
    selected_ids = {entry["sample_id"] for entry in selected_files}
    remaining_files = [dict(entry) for entry in render_files if entry["sample_id"] not in selected_ids]

    def _score(entry: dict) -> int:
        sample_data = sample_by_path[entry["path"]]
        return _selection_score(entry, sample_data, duplicate_counts)

    def _replace(victim_index: int, replacement: dict, reason: str) -> None:
        victim = selected_files[victim_index]
        remaining_files.append(victim)
        selected_files[victim_index] = replacement
        remaining_files.remove(replacement)
        selection_reasons[replacement["sample_id"]] = reason

    selected_checksums = Counter(sample_by_path[entry["path"]]["checksum_sha256"] for entry in selected_files)
    for index, entry in enumerate(list(selected_files)):
        checksum = sample_by_path[entry["path"]]["checksum_sha256"]
        if selected_checksums[checksum] <= 1:
            continue
        replacement = next(
            (
                candidate
                for candidate in sorted(remaining_files, key=_score, reverse=True)
                if candidate["class_name"] == entry["class_name"]
                and candidate["framing"] == entry["framing"]
                and sample_by_path[candidate["path"]]["checksum_sha256"] != checksum
            ),
            None,
        )
        if replacement is None:
            continue
        selected_checksums[checksum] -= 1
        selected_checksums[sample_by_path[replacement["path"]]["checksum_sha256"]] += 1
        _replace(index, replacement, "curated_for_duplicate_reduction")

    for required_angle in ("front", "left_three_quarter", "right_three_quarter", "left_profile", "right_profile"):
        while Counter(str(entry.get("camera_angle")) for entry in selected_files).get(required_angle, 0) < 4:
            replacement = next(
                (
                    candidate
                    for candidate in sorted(remaining_files, key=_score, reverse=True)
                    if candidate["camera_angle"] == required_angle
                ),
                None,
            )
            if replacement is None:
                break
            victim_index = next(
                (
                    idx
                    for idx, candidate in enumerate(selected_files)
                    if candidate["class_name"] == replacement["class_name"]
                    and candidate["framing"] == replacement["framing"]
                    and Counter(str(entry.get("camera_angle")) for entry in selected_files).get(str(candidate.get("camera_angle")), 0) > 4
                ),
                None,
            )
            if victim_index is None:
                break
            _replace(victim_index, replacement, "curated_for_angle_coverage")

    selected_ids = {entry["sample_id"] for entry in selected_files}
    rejected_sample_ids = [entry["sample_id"] for entry in render_files if entry["sample_id"] not in selected_ids]
    angle_counts = Counter(str(entry.get("camera_angle")) for entry in selected_files)
    framing_counts = Counter(str(entry.get("framing")) for entry in selected_files)
    duplicate_share = 0.0
    if selected_files:
        selected_duplicates = Counter(sample_by_path[entry["path"]]["checksum_sha256"] for entry in selected_files)
        duplicate_share = max(selected_duplicates.values()) / len(selected_files)
    review_required = (
        len(selected_files) != target
        or framing_counts.get("full_body", 0) < 20
        or any(angle_counts.get(angle, 0) < 4 for angle in ("front", "left_three_quarter", "right_three_quarter", "left_profile", "right_profile"))
        or duplicate_share > 0.10
    )
    return selected_files, rejected_sample_ids, selection_reasons, review_required


def _validate_dataset_manifest_contract(dataset_manifest: dict) -> None:
    files = dataset_manifest.get("files") or []
    if not files:
        raise ValueError("dataset builder did not produce any files")
    required_fields = {
        "sample_id",
        "path",
        "seed",
        "prompt",
        "negative_prompt",
        "caption",
        "wardrobe_state",
        "framing",
        "camera_angle",
        "pose_family",
        "camera_distance",
        "lens_hint",
        "lighting_setup",
        "background_style",
        "quality_priority",
        "realism_profile",
        "source_strategy",
    }
    if any(any(field not in entry for field in required_fields) for entry in files):
        raise ValueError("dataset builder requires prompt, caption, seed and coverage metadata for every sample")
    counts = _classify_dataset_samples(dataset_manifest)
    if counts["SFW"] != counts["NSFW"]:
        raise ValueError("dataset builder requires a 50/50 balance between SFW and NSFW")
    if counts["SFW"] + counts["NSFW"] != int(dataset_manifest.get("sample_count", 0)):
        raise ValueError("dataset builder sample_count does not match the generated file list")
    framing_counts = Counter(str(entry.get("framing")) for entry in files)
    if int(dataset_manifest.get("render_sample_count", 0)) < 80:
        raise ValueError("dataset builder requires at least 80 rendered samples before curation")
    if int(dataset_manifest.get("selected_sample_count", 0)) != int(dataset_manifest.get("sample_count", 0)):
        raise ValueError("selected_sample_count must match sample_count in the curated manifest")
    if framing_counts.get("full_body", 0) < 20:
        raise ValueError("dataset builder requires at least 20 curated full_body samples")
    angle_counts = Counter(str(entry.get("camera_angle")) for entry in files)
    if any(angle_counts.get(angle, 0) < 4 for angle in ("front", "left_three_quarter", "right_three_quarter", "left_profile", "right_profile")):
        raise ValueError("dataset builder requires all five camera angles in the curated subset")


def _materialize_dataset_package(
    *,
    dataset_manifest: dict,
    base_image_bytes: bytes,
    dataset_samples: list[dict],
    manifest_path: Path,
    package_path: Path,
    render_manifest_path: Path | None = None,
    render_package_path: Path | None = None,
    source_base_image_path: Path,
) -> tuple[Path, int]:
    source_base_image_path.parent.mkdir(parents=True, exist_ok=True)
    source_base_image_path.write_bytes(base_image_bytes)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    package_path.parent.mkdir(parents=True, exist_ok=True)

    samples_by_path = {sample["path"]: sample for sample in dataset_samples}
    render_files = list(dataset_manifest.get("render_files") or [])
    for file_entry in render_files:
        sample_data = samples_by_path.get(file_entry["path"])
        if sample_data is None:
            raise RuntimeError(f"COMFYUI_EXECUTION_FAILED: missing generated bytes for dataset sample {file_entry['path']}")
        sample_path = manifest_path.parent / Path(file_entry["path"])
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        sample_path.write_bytes(sample_data["bytes"])
        file_entry["checksum_sha256"] = sample_data["checksum_sha256"]
        file_entry["byte_size"] = sample_data["byte_size"]
        file_entry["provider_job_id"] = sample_data["provider_job_id"]
        file_entry["source_uri"] = sample_data["source_uri"]
    for file_entry in dataset_manifest["files"]:
        sample_data = samples_by_path.get(file_entry["path"])
        if sample_data is None:
            continue
        file_entry["checksum_sha256"] = sample_data["checksum_sha256"]
        file_entry["byte_size"] = sample_data["byte_size"]
        file_entry["provider_job_id"] = sample_data["provider_job_id"]
        file_entry["source_uri"] = sample_data["source_uri"]

    if render_manifest_path is not None:
        render_manifest_path.write_text(json.dumps(dataset_manifest, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(dataset_manifest, indent=2), encoding="utf-8")
    if render_package_path is not None:
        with zipfile.ZipFile(render_package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(source_base_image_path, arcname="base-image.png")
            if render_manifest_path is not None:
                archive.write(render_manifest_path, arcname="render-manifest.json")
            for file_entry in render_files:
                sample_path = manifest_path.parent / Path(file_entry["path"])
                archive.write(sample_path, arcname=file_entry["path"])
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(source_base_image_path, arcname="base-image.png")
        archive.write(manifest_path, arcname="dataset-manifest.json")
        for file_entry in dataset_manifest["files"]:
            sample_path = manifest_path.parent / Path(file_entry["path"])
            archive.write(sample_path, arcname=file_entry["path"])

    return package_path, package_path.stat().st_size


def _maybe_attach_dataset_handoff(
    job_input: dict,
    result: dict,
    *,
    emit_progress: ProgressEmitter | None = None,
) -> dict:
    identity_id = _resolve_identity_id(job_input)
    character_id = _resolve_character_id(job_input)
    result.setdefault("metadata", {})
    result["metadata"].setdefault("persisted_artifacts", [])
    if identity_id is None:
        result["metadata"]["dataset_handoff_ready"] = False
        result["metadata"]["dataset_handoff_reason"] = "identity_id was not provided"
        return result

    artifacts = result.get("artifacts") or []
    base_image_bytes = _resolve_base_image_bytes(artifacts)
    if base_image_bytes is None:
        result["metadata"]["dataset_handoff_ready"] = False
        result["metadata"]["dataset_handoff_reason"] = "base_image artifact is not materializable"
        return result

    metadata = job_input.get("metadata") or {}
    training_samples_target = int(metadata.get("samples_target", job_input.get("samples_target", 40)))
    render_samples_target = int(metadata.get("render_samples_target", job_input.get("render_samples_target", 80)))
    dataset_workflow_id = str(metadata.get("dataset_workflow_id") or job_input.get("dataset_workflow_id") or "lora-dataset-ipadapter-batch")
    dataset_workflow_version = str(metadata.get("dataset_workflow_version") or job_input.get("dataset_workflow_version") or "2026-04-08")
    identity_root = ARTIFACT_ROOT / str(identity_id)
    seed_bundle = _seed_bundle_from_job_input(job_input)
    dataset_version = f"dataset-{_sha256_bytes(base_image_bytes + str(seed_bundle.dataset_seed).encode('utf-8'))[:12]}"
    dataset_shot_plan = build_dataset_shot_plan(
        dataset_version=dataset_version,
        avatar_identity_block=str(job_input.get("prompt", "editorial portrait of a synthetic premium performer")),
        base_negative_prompt=str(
            job_input.get("negative_prompt", "low quality, anatomy drift, extra limbs, text, watermark")
        ),
        seed_bundle=seed_bundle,
        samples_target=render_samples_target,
    )
    generation_manifest = GenerationManifest(
        identity_id=identity_id,
        prompt=str(job_input.get("prompt", "editorial portrait of a synthetic premium performer")),
        negative_prompt=str(job_input.get("negative_prompt", "low quality, anatomy drift, extra limbs, text, watermark")),
        seed_bundle=seed_bundle,
        samples_target=training_samples_target,
        render_samples_target=render_samples_target,
        training_samples_target=training_samples_target,
        training_target_count=training_samples_target,
        selection_policy=str(metadata.get("selection_policy") or job_input.get("selection_policy") or "score_curated_v1"),
        workflow_id=dataset_workflow_id,
        workflow_version=dataset_workflow_version,
        workflow_family=str(job_input.get("workflow_family", "flux_lora_dataset_reference")),
        workflow_registry_source=str(job_input.get("workflow_registry_source", "approved_internal")),
        base_model_id=str(job_input.get("base_model_id", "flux-schnell-v1")),
        realism_profile=str(job_input.get("realism_profile", "photorealistic_adult_reference_v1")),
        source_strategy=str(job_input.get("source_strategy", "avatar_prompt_plus_shot_plan_v2")),
        render_shot_plan=dataset_shot_plan,
        comfy_parameters={
            "width": int(job_input.get("width", 1024)),
            "height": int(job_input.get("height", 1024)),
            "reference_face_image_url": job_input.get("reference_face_image_url"),
            "ip_adapter": job_input.get("ip_adapter", {}),
            "face_detailer": job_input.get("face_detailer", {}),
            "workflow_family": job_input.get("workflow_family"),
            "workflow_registry_source": job_input.get("workflow_registry_source"),
            "copilot_prompt_template": job_input.get("copilot_prompt_template"),
            "copilot_negative_prompt": job_input.get("copilot_negative_prompt"),
            "selection_policy": metadata.get("selection_policy") or job_input.get("selection_policy") or "score_curated_v1",
            "render_samples_target": render_samples_target,
            "training_samples_target": training_samples_target,
        },
        artifact_path=(identity_root / "generation-manifest.json").as_posix(),
    )
    dataset_input = DatasetServiceInput(
        identity_id=identity_id,
        generation_manifest=generation_manifest,
        reference_face_image_url=job_input.get("reference_face_image_url"),
        samples_target=training_samples_target,
        render_samples_target=render_samples_target,
        training_samples_target=training_samples_target,
        selection_policy=str(metadata.get("selection_policy") or job_input.get("selection_policy") or "score_curated_v1"),
        render_shot_plan=dataset_shot_plan,
        face_detection_confidence=result.get("face_detection_confidence"),
        artifact_root=ARTIFACT_ROOT.as_posix(),
        metadata_json={
            "provider_job_id": result.get("provider_job_id"),
            "workflow_scope": "s1_image",
            "autopromote_candidate": bool(metadata.get("autopromote", False)),
            "character_id": character_id or str(identity_id),
            "seed_bundle": seed_bundle.model_dump(mode="json"),
            "workflow_extensions": ["ComfyUI-BatchingNodes", "ComfyPack"],
            "workflow_family": generation_manifest.workflow_family,
            "workflow_registry_source": generation_manifest.workflow_registry_source,
        },
    )
    dataset_result = build_dataset_result(dataset_input)
    manifest = dataset_result["dataset_manifest"]
    manifest_path = Path(manifest["artifact_path"])
    package_path = Path(manifest["dataset_package_path"])
    render_manifest_path = Path(manifest["render_manifest_path"])
    render_package_path = Path(manifest["render_package_path"])
    base_image_path = manifest_path.parent / "base-image.png"
    manifest["review_required"] = not bool(metadata.get("autopromote", False))
    dataset_samples = _generate_dataset_samples(
        job_input=job_input,
        dataset_manifest=manifest,
        base_image_bytes=base_image_bytes,
        emit_progress=emit_progress,
    )
    selected_files, rejected_sample_ids, selection_reasons, curation_review_required = _curate_training_subset(manifest, dataset_samples)
    manifest["files"] = selected_files
    manifest["generated_samples"] = len(selected_files)
    manifest["selected_sample_count"] = len(selected_files)
    manifest["sample_count"] = len(selected_files)
    manifest["rejected_sample_ids"] = rejected_sample_ids
    manifest["selection_reasons"] = selection_reasons
    render_framing_counts = Counter(str(entry.get("framing")) for entry in manifest.get("render_files", []))
    selected_framing_counts = Counter(str(entry.get("framing")) for entry in selected_files)
    render_angle_counts = Counter(str(entry.get("camera_angle")) for entry in manifest.get("render_files", []))
    selected_angle_counts = Counter(str(entry.get("camera_angle")) for entry in selected_files)
    manifest["coverage_summary"] = {
        "rendered": {
            "angles": dict(render_angle_counts),
            "framing": dict(render_framing_counts),
            "wardrobe_state": dict(Counter(str(entry.get("wardrobe_state")) for entry in manifest.get("render_files", []))),
        },
        "selected": {
            "angles": dict(selected_angle_counts),
            "framing": dict(selected_framing_counts),
            "wardrobe_state": dict(Counter(str(entry.get("wardrobe_state")) for entry in selected_files)),
        },
    }
    manifest["review_required"] = manifest["review_required"] or curation_review_required
    _validate_dataset_manifest_contract(manifest)
    package_path, package_size = _materialize_dataset_package(
        dataset_manifest=manifest,
        base_image_bytes=base_image_bytes,
        dataset_samples=dataset_samples,
        manifest_path=manifest_path,
        package_path=package_path,
        render_manifest_path=render_manifest_path,
        render_package_path=render_package_path,
        source_base_image_path=base_image_path,
    )
    package_checksum = _sha256_bytes(package_path.read_bytes())

    materialized_artifacts = []
    for artifact in dataset_result["artifacts"]:
        artifact_copy = dict(artifact)
        artifact_copy.setdefault("metadata_json", {})
        artifact_copy["metadata_json"].update(
            {
                "identity_id": str(identity_id),
                "character_id": character_id or str(identity_id),
                "seed_bundle": seed_bundle.model_dump(mode="json"),
            }
        )
        if artifact_copy["artifact_type"] == "base_image":
            artifact_copy["storage_path"] = base_image_path.as_posix()
            artifact_copy["size_bytes"] = len(base_image_bytes)
            artifact_copy["metadata_json"]["inline_data_base64"] = base64.b64encode(base_image_bytes).decode("ascii")
        elif artifact_copy["artifact_type"] == "dataset_manifest":
            artifact_copy["storage_path"] = manifest_path.as_posix()
            artifact_copy["size_bytes"] = manifest_path.stat().st_size
            artifact_copy["metadata_json"]["dataset_version"] = manifest["dataset_version"]
            artifact_copy["metadata_json"]["composition"] = manifest["composition"]
        elif artifact_copy["artifact_type"] == "dataset_package":
            artifact_copy["storage_path"] = package_path.as_posix()
            artifact_copy["checksum_sha256"] = package_checksum
            artifact_copy["size_bytes"] = package_size
            artifact_copy["metadata_json"]["dataset_version"] = manifest["dataset_version"]
        materialized_artifacts.append(artifact_copy)

    manifest["checksum_sha256"] = package_checksum
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    result["generation_manifest"] = generation_manifest.model_dump(mode="json")
    result["dataset_manifest"] = manifest
    result["dataset_package_path"] = package_path.as_posix()
    result["dataset_artifacts"] = materialized_artifacts
    result["metadata"]["dataset_handoff_ready"] = True
    result["metadata"]["dataset_storage_mode"] = "local_artifact_root"
    result["metadata"]["dataset_review_required"] = manifest["review_required"]
    result["metadata"]["dataset_version"] = manifest["dataset_version"]
    result["metadata"]["dataset_composition"] = manifest["composition"]
    result["metadata"]["identity_id"] = str(identity_id)
    result["metadata"]["character_id"] = character_id or str(identity_id)
    result["metadata"]["seed_bundle"] = seed_bundle.model_dump(mode="json")
    result["metadata"]["samples_target"] = training_samples_target
    result["metadata"]["render_samples_target"] = render_samples_target
    result["metadata"]["selection_policy"] = generation_manifest.selection_policy
    result["metadata"]["render_package_path"] = render_package_path.as_posix()
    return result


def _run_generation(job_input: dict, *, emit_progress: ProgressEmitter | None = None) -> dict:
    _emit_progress(emit_progress, stage="validating_runtime_contract", message="Validating S1 image runtime contract", progress=0.16)
    _assert_s1_runtime_contract(job_input)
    _emit_progress(emit_progress, stage="starting_runtime", message="Preparing ComfyUI runtime", progress=0.2)
    _ensure_comfyui_running(emit_progress=emit_progress, job_input=job_input)
    _emit_progress(emit_progress, stage="validating_runtime_assets", message="Checking FLUX and IP Adapter assets", progress=0.32)
    _assert_required_runtime_inputs(job_input)

    mode = str(job_input.get("mode", ResumeStage.BASE_RENDER.value))
    _emit_progress(emit_progress, stage="building_workflow", message=f"Preparing {mode} workflow payload", progress=0.42)
    workflow = _build_workflow_payload(job_input)
    _emit_progress(emit_progress, stage="submitting_prompt", message="Submitting prompt to ComfyUI", progress=0.54)
    prompt_id = _submit_prompt(workflow, mode=mode, job_input=job_input)
    _emit_progress(emit_progress, stage="awaiting_history", message=f"Waiting for ComfyUI prompt {prompt_id}", progress=0.7)
    history = _poll_history(prompt_id)
    _emit_progress(emit_progress, stage="collecting_artifacts", message="Collecting generated artifacts", progress=0.84)
    artifacts = _extract_artifacts(history, mode=mode)
    if not artifacts:
        raise RuntimeError("COMFYUI_EXECUTION_FAILED: ComfyUI execution did not expose any artifacts")

    face_detection_confidence = _extract_face_confidence(history, job_input)
    face_confidence_inferred = False
    if mode == ResumeStage.BASE_RENDER.value and face_detection_confidence is None and artifacts:
        face_detection_confidence = float(
            job_input.get("face_confidence_threshold", COMFYUI_FACE_CONFIDENCE_THRESHOLD)
        )
        face_confidence_inferred = True
    if mode == ResumeStage.BASE_RENDER.value and face_detection_confidence is None:
        _emit_progress(emit_progress, stage="face_confidence_missing", message="Face detector did not return a usable score", progress=0.92)
        return _response_error(
            "FACE_CONFIDENCE_UNAVAILABLE",
            "face detector did not return a usable confidence score",
            {"prompt_id": prompt_id},
            job_input=job_input,
        )
    if mode == ResumeStage.BASE_RENDER.value:
        _emit_progress(
            emit_progress,
            stage="base_render_complete",
            message=f"Base render finished with face confidence {face_detection_confidence:.2f}",
            progress=0.94,
        )
    else:
        _emit_progress(emit_progress, stage="face_detail_complete", message="Face detail stage completed", progress=0.94)

    successful_node_ids = list(history.get("outputs", {}).keys())
    checkpoint_stage = ResumeStage.BASE_RENDER if mode == ResumeStage.BASE_RENDER.value else ResumeStage.COMPLETED
    resume_checkpoint = _build_resume_checkpoint(
        job_input=job_input,
        artifacts=artifacts,
        prompt_id=prompt_id,
        successful_node_ids=successful_node_ids,
        stage=checkpoint_stage,
        face_detection_confidence=face_detection_confidence,
    )

    result = {
        "provider": Provider.MODAL.value,
        "workflow_id": _resolved_workflow_id(job_input),
        "workflow_version": _resolved_workflow_version(job_input),
        "base_model_id": str(job_input.get("base_model_id", "flux-schnell-v1")),
        "model_family": "flux",
        "runtime_stage": RuntimeStage.IDENTITY_IMAGE.value,
        "seed": int(job_input.get("seed", 42)),
        "service_runtime": "s1_image",
        "provider_job_id": prompt_id,
        "prompt_id": prompt_id,
        "artifacts": artifacts,
        "successful_node_ids": successful_node_ids,
        "face_detection_confidence": face_detection_confidence,
        "ip_adapter_used": bool(job_input.get("reference_face_image_url")),
        "regional_inpaint_triggered": mode == ResumeStage.FACE_DETAIL.value,
        "resume_checkpoint": resume_checkpoint,
        "metadata": {
            "mode": mode,
            "model_family": "flux",
            "runtime_stage": RuntimeStage.IDENTITY_IMAGE.value,
            "workflow_scope": "s1_image",
            "service_runtime": "s1_image",
            "identity_id": str(_resolve_identity_id(job_input)) if _resolve_identity_id(job_input) is not None else None,
            "character_id": _resolve_character_id(job_input),
            "requested_threshold": job_input.get("face_confidence_threshold", COMFYUI_FACE_CONFIDENCE_THRESHOLD),
            "face_detection_confidence_inferred": face_confidence_inferred,
            "workflow_id": _resolved_workflow_id(job_input),
            "workflow_version": _resolved_workflow_version(job_input),
            "workflow_family": str(job_input.get("workflow_family", "flux_identity_reference")),
            "workflow_registry_source": str(job_input.get("workflow_registry_source", "approved_internal")),
            "base_model_id": str(job_input.get("base_model_id", "flux-schnell-v1")),
            "seed": int(job_input.get("seed", 42)),
            "seed_bundle": _seed_bundle_from_job_input(job_input).model_dump(mode="json"),
            "prompt": str(job_input.get("prompt", "")),
            "negative_prompt": str(job_input.get("negative_prompt", "")),
            "width": int(job_input.get("width", 1024)),
            "height": int(job_input.get("height", 1024)),
            "ip_adapter": job_input.get("ip_adapter", {}),
            "face_detailer": job_input.get("face_detailer", {}),
            "reference_face_image_url": job_input.get("reference_face_image_url"),
            "realism_profile": str(job_input.get("realism_profile", "photorealistic_adult_reference_v1")),
            "source_strategy": str(job_input.get("source_strategy", "avatar_prompt_plus_shot_plan_v1")),
            "copilot_prompt_template": job_input.get("copilot_prompt_template"),
            "copilot_negative_prompt": job_input.get("copilot_negative_prompt"),
            "flux_assets": {
                "diffusion_model": job_input.get("flux_diffusion_model_name", COMFYUI_FLUX_DIFFUSION_MODEL_NAME),
                "ae": job_input.get("flux_ae_name", COMFYUI_FLUX_AE_NAME),
                "clip_l": job_input.get("flux_clip_l_name", COMFYUI_FLUX_CLIP_L_NAME),
                "t5xxl": job_input.get("flux_t5xxl_name", COMFYUI_FLUX_T5XXL_NAME),
                "ip_adapter": _resolve_ip_adapter_model_name(job_input),
            },
        },
    }
    if mode == ResumeStage.BASE_RENDER.value:
        result = _maybe_attach_dataset_handoff(job_input, result, emit_progress=emit_progress)
    return result


def _run_generation_via_modal(job_input: dict, *, emit_progress: ProgressEmitter | None = None) -> dict:
    try:
        import modal
    except Exception as exc:
        raise RuntimeError(f"COMFYUI_EXECUTION_FAILED: modal backend is not available in this runtime ({exc})") from exc

    _emit_progress(emit_progress, stage="dispatching_modal_job", message="Dispatching S1 image job to Modal GPU worker", progress=0.2)
    modal_function = modal.Function.from_name(S1_IMAGE_MODAL_APP_NAME, S1_IMAGE_MODAL_FUNCTION_NAME)
    result = modal_function.remote(job_input)
    metadata = result.get("metadata", {})
    remote_events = metadata.pop("modal_progress_events", []) if isinstance(metadata, dict) else []
    for event in remote_events:
        stage = str(event.get("stage", "modal_worker"))
        message = str(event.get("message", stage))
        progress = float(event.get("progress", 0.5))
        _emit_progress(emit_progress, stage=stage, message=message, progress=progress)
    _emit_progress(emit_progress, stage="modal_job_completed", message="Modal GPU worker finished S1 image job", progress=0.96)
    return result


def _processor(payload: dict, *, emit_progress: ProgressEmitter | None = None) -> dict:
    try:
        action = str(payload.get("action", "generate"))
        if action != "generate":
            return _response_error("COMFYUI_EXECUTION_FAILED", f"unsupported action {action}", job_input=payload)
        if S1_IMAGE_EXECUTION_BACKEND == "modal":
            return _run_generation_via_modal(payload, emit_progress=emit_progress)
        return _run_generation(payload, emit_progress=emit_progress)
    except FileNotFoundError as exc:
        return _response_error("REFERENCE_IMAGE_NOT_FOUND", str(exc), job_input=payload)
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith("RESUME_STATE_INCOMPLETE:"):
            return _response_error("RESUME_STATE_INCOMPLETE", message.split(":", 1)[1].strip(), job_input=payload)
        if message.startswith("COMFYUI_EXECUTION_FAILED:"):
            return _response_error("COMFYUI_EXECUTION_FAILED", message.split(":", 1)[1].strip(), job_input=payload)
        return _response_error("COMFYUI_EXECUTION_FAILED", message, job_input=payload)
    except Exception as exc:
        return _response_error("COMFYUI_EXECUTION_FAILED", str(exc), job_input=payload)


def _enum_or_value(value: object) -> object:
    return getattr(value, "value", value)


def _directus_base_url() -> str:
    base_url = os.getenv("DIRECTUS_BASE_URL", "").strip()
    if not base_url or base_url == "CHANGEME":
        raise RuntimeError("DIRECTUS_BASE_URL must be configured before enabling web login")
    return base_url.rstrip("/")


def _directus_request_json(
    method: str,
    url: str,
    *,
    payload: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: int = 30,
) -> dict[str, object]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json", **(headers or {})},
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


def _directus_login(email: str, password: str) -> dict[str, object]:
    response = _directus_request_json(
        "POST",
        f"{_directus_base_url()}/auth/login",
        payload={"email": email, "password": password},
    )
    data = response.get("data")
    if not isinstance(data, dict) or not data.get("access_token"):
        raise RuntimeError("Directus login response did not include an access_token")
    return data


def _directus_me(access_token: str) -> dict[str, object]:
    response = _directus_request_json(
        "GET",
        f"{_directus_base_url()}/users/me?fields=id,email,first_name,last_name,status",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    data = response.get("data")
    if not isinstance(data, dict) or not data.get("email"):
        raise RuntimeError("Directus user response did not include an email")
    return data


def _auth_cookie_value(session_id: str) -> str:
    signature = hmac.new(WEB_SESSION_SECRET.encode("utf-8"), session_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{session_id}.{signature}"


def _auth_session_id_from_cookie(cookie_value: str | None) -> str | None:
    if not cookie_value or "." not in cookie_value:
        return None
    session_id, signature = cookie_value.rsplit(".", 1)
    expected = hmac.new(WEB_SESSION_SECRET.encode("utf-8"), session_id.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    return session_id


def _prune_auth_sessions() -> None:
    now = time.time()
    expired = [session_id for session_id, payload in _WEB_AUTH_SESSIONS.items() if float(payload.get("expires_at", 0)) <= now]
    for session_id in expired:
        _WEB_AUTH_SESSIONS.pop(session_id, None)


def _create_auth_session(user_payload: dict[str, object], auth_payload: dict[str, object]) -> tuple[str, dict[str, object]]:
    _prune_auth_sessions()
    session_id = uuid.uuid4().hex
    session = {
        "session_id": session_id,
        "email": str(user_payload.get("email", "")),
        "user_id": str(user_payload.get("id", "")),
        "first_name": str(user_payload.get("first_name", "") or ""),
        "last_name": str(user_payload.get("last_name", "") or ""),
        "status": str(user_payload.get("status", "") or ""),
        "access_token": str(auth_payload.get("access_token", "")),
        "expires_at": time.time() + WEB_SESSION_TTL_SECONDS,
    }
    _WEB_AUTH_SESSIONS[session_id] = session
    return session_id, session


def _auth_identity(session: dict[str, object]) -> dict[str, object]:
    display_name = " ".join(
        bit for bit in [str(session.get("first_name", "")).strip(), str(session.get("last_name", "")).strip()] if bit
    )
    return {
        "email": session.get("email"),
        "user_id": session.get("user_id"),
        "first_name": session.get("first_name"),
        "last_name": session.get("last_name"),
        "display_name": display_name or session.get("email"),
        "status": session.get("status"),
    }


def _set_auth_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=WEB_SESSION_COOKIE_NAME,
        value=_auth_cookie_value(session_id),
        httponly=True,
        secure=WEB_SESSION_SECURE,
        samesite="lax",
        max_age=WEB_SESSION_TTL_SECONDS,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=WEB_SESSION_COOKIE_NAME, path="/", samesite="lax")


def _active_auth_session(request_obj: Request) -> dict[str, object] | None:
    _prune_auth_sessions()
    session_id = _auth_session_id_from_cookie(request_obj.cookies.get(WEB_SESSION_COOKIE_NAME))
    if session_id is None:
        return None
    session = _WEB_AUTH_SESSIONS.get(session_id)
    if session is None or float(session.get("expires_at", 0)) <= time.time():
        _WEB_AUTH_SESSIONS.pop(session_id, None)
        return None
    return session


def _require_auth(request_obj: Request) -> dict[str, object]:
    session = _active_auth_session(request_obj)
    if session is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return session


def _lab_session_store(session_id: str) -> dict[str, object]:
    return _LAB_SESSIONS.setdefault(session_id, {})


_LAB_REQUIRED_MANUAL_FIELDS: tuple[str, ...] = (
    "identity_core.fictional_age_years",
    "metadata.category",
    "metadata.vertical",
    "metadata.occupation_or_content_basis",
    "voice_tone",
    "communication_style.speech_style",
    "visual_profile.eye_color",
    "visual_profile.hair_color",
)

_LAB_MISSING_FIELD_QUESTIONS_BY_LOCALE: dict[str, dict[str, str]] = {
    "en": {
        "identity_core.fictional_age_years": "Tell me the fictional adult age you want to use.",
        "metadata.occupation_or_content_basis": "Tell me the profession or content basis to close the draft.",
        "metadata.vertical": "Confirm the avatar's main content type.",
        "metadata.category": "Confirm the avatar's commercial category.",
        "voice_tone": "Tell me the main voice tone, for example formal or seductive.",
        "communication_style.speech_style": "Tell me the speech style, for example formal, casual, or glam.",
        "visual_profile.eye_color": "Tell me the eye color you want to use.",
        "visual_profile.hair_color": "Tell me the hair color you want to use.",
        "conversation.scene_context": "Tell me the main setting or scene, for example in her studio.",
    },
    "es": {
        "identity_core.fictional_age_years": "Decime la edad adulta ficticia que queres usar.",
        "metadata.occupation_or_content_basis": "Decime la profesion o base de contenido para cerrar la ficha.",
        "metadata.vertical": "Confirmame el tipo de contenido principal del avatar.",
        "metadata.category": "Confirmame la categoria comercial del avatar.",
        "voice_tone": "Indicame el tono de voz principal, por ejemplo formal o seductor.",
        "communication_style.speech_style": "Indicame el estilo de habla, por ejemplo formal, casual o glam.",
        "visual_profile.eye_color": "Decime el color de ojos que queres usar.",
        "visual_profile.hair_color": "Decime el color de pelo que queres usar.",
        "conversation.scene_context": "Contame en que contexto o escena principal opera, por ejemplo en su estudio.",
    },
}

_LAB_FIELD_LABELS_BY_LOCALE: dict[str, dict[str, str]] = {
    "en": {
        "identity_core.fictional_age_years": "Fictional age",
        "metadata.category": "Commercial category",
        "metadata.vertical": "Content type",
        "metadata.occupation_or_content_basis": "Profession or content basis",
        "voice_tone": "Voice tone",
        "communication_style.speech_style": "Speech style",
        "visual_profile.eye_color": "Eye color",
        "visual_profile.hair_color": "Hair color",
        "conversation.scene_context": "Main setting or scene",
    },
    "es": {
        "identity_core.fictional_age_years": "Edad ficticia",
        "metadata.category": "Categoria comercial",
        "metadata.vertical": "Tipo de contenido",
        "metadata.occupation_or_content_basis": "Profesion o base de contenido",
        "voice_tone": "Tono de voz",
        "communication_style.speech_style": "Estilo de habla",
        "visual_profile.eye_color": "Color de ojos",
        "visual_profile.hair_color": "Color de pelo",
        "conversation.scene_context": "Contexto o escena principal",
    },
}

_LAB_UI_TEXT_BY_LOCALE: dict[str, dict[str, str]] = {
    "en": {
        "no_reference": "No reference",
        "operator_context_title": "Accumulated operator context for VixenBliss Creator:",
        "turn_label": "Turn",
        "failed_turn": "I could not update the draft with this turn. Check the error and we can try another adjustment.",
        "draft_created": "I built an evolving draft.",
        "draft_updated": "I updated the draft for {display_name}.",
        "detected_changes": " Detected changes: {changes}.",
        "not_ready": " It is not ready for S1 Image yet. Still missing: {missing}.",
        "ready": " The draft is now ready to send to S1 Image whenever you want.",
        "autofill_hint": " You can also say 'complete the rest automatically'.",
        "failed_conversational_turn": "I could not update the conversational draft on this turn.",
        "no_previous_run": "There is no previous LangGraph run for this session.",
        "graph_not_ready": "The latest GraphState is not ready for handoff.",
        "handoff_not_ready": "The conversational draft is not ready for handoff yet. Still missing: {missing}.",
        "avatar_fallback": "the avatar",
    },
    "es": {
        "no_reference": "Sin referencia",
        "operator_context_title": "Contexto acumulado del operador para VixenBliss Creator:",
        "turn_label": "Turno",
        "failed_turn": "No pude actualizar el draft con este turno. Revisa el error y probamos otro ajuste.",
        "draft_created": "Arme un draft evolutivo.",
        "draft_updated": "Actualice el draft de {display_name}.",
        "detected_changes": " Cambios detectados: {changes}.",
        "not_ready": " Todavia no esta lista para S1 Image. Faltan: {missing}.",
        "ready": " La ficha ya quedo lista para enviar a S1 Image cuando quieras.",
        "autofill_hint": " Tambien podes decir 'completa el resto automaticamente'.",
        "failed_conversational_turn": "No pude actualizar el draft conversacional en este turno.",
        "no_previous_run": "No hay una ejecucion previa de LangGraph para esta sesion.",
        "graph_not_ready": "El ultimo GraphState no quedo listo para handoff.",
        "handoff_not_ready": "La ficha conversacional todavia no esta lista para handoff. Faltan: {missing}.",
        "avatar_fallback": "el avatar",
    },
}


def _lab_normalize_locale(value: object) -> str:
    normalized = str(value or "en").strip().lower()
    if normalized.startswith("es"):
        return "es"
    return "en"


def _lab_text(locale: str, key: str, **kwargs: object) -> str:
    language = _lab_normalize_locale(locale)
    template = _LAB_UI_TEXT_BY_LOCALE.get(language, _LAB_UI_TEXT_BY_LOCALE["en"]).get(key, key)
    return template.format(**kwargs) if kwargs else template


def _lab_field_label(field_path: str, *, locale: str) -> str:
    language = _lab_normalize_locale(locale)
    labels = _LAB_FIELD_LABELS_BY_LOCALE.get(language, _LAB_FIELD_LABELS_BY_LOCALE["en"])
    return labels.get(field_path, field_path)


def _lab_turn_source_text(message: str) -> str:
    return normalize_trace_source_text(message) or "turno_operador"


def _lab_autofill_requested(message: str) -> bool:
    normalized = " ".join(message.lower().split())
    return any(
        term in normalized
        for term in (
            "completa el resto",
            "completá el resto",
            "rellena el resto",
            "rellená el resto",
            "resto automatic",
            "resto automático",
            "autocompleta",
            "autocompletá",
            "hacelo automatic",
            "hacelo automático",
        )
    )


def _lab_extract_turn_updates(message: str) -> dict[str, dict[str, object]]:
    normalized = " ".join(message.lower().split())
    source_text = _lab_turn_source_text(message)
    updates: dict[str, dict[str, object]] = {}

    age_match = re.search(r"\b([1-9]\d)\s*a(?:n|ñ)os\b", normalized)
    if age_match:
        age_value = int(age_match.group(1))
        if 18 <= age_value <= 99:
            updates["identity_core.fictional_age_years"] = {"value": age_value, "source_text": source_text}

    if "nsfw" in normalized or "adult" in normalized:
        updates["metadata.vertical"] = {"value": "adult_entertainment", "source_text": source_text}
        updates["metadata.category"] = {"value": "adult_creator", "source_text": source_text}

    if "formal" in normalized:
        updates["voice_tone"] = {"value": "formal", "source_text": source_text}
        updates["communication_style.speech_style"] = {"value": "refined", "source_text": source_text}
    elif "seduct" in normalized or "sensual" in normalized:
        updates["voice_tone"] = {"value": "seductive", "source_text": source_text}

    if "psicolog" in normalized:
        occupation = "licenciada en psicologia" if "licenciada" in normalized else "psicologa"
        updates["metadata.occupation_or_content_basis"] = {"value": occupation, "source_text": source_text}
    elif "secretari" in normalized:
        updates["metadata.occupation_or_content_basis"] = {"value": "secretaria", "source_text": source_text}

    if "estudio" in normalized or "studio" in normalized:
        updates["conversation.scene_context"] = {"value": "en su estudio", "source_text": source_text}

    for terms, color in (
        (("ojos verdes", "ojos color verde", "green eyes"), "green"),
        (("ojos azules", "ojos color azul", "blue eyes"), "blue"),
        (("ojos marrones", "ojos cafes", "ojos café", "brown eyes"), "brown"),
        (("ojos avellana", "hazel eyes"), "hazel"),
    ):
        if any(term in normalized for term in terms):
            updates["visual_profile.eye_color"] = {"value": color, "source_text": source_text}
            break

    for terms, color in (
        (("rubia", "rubio", "blonde", "blond"), "blonde"),
        (("pelirroja", "pelirrojo", "redhead", "red hair", "ginger"), "red"),
        (("morena", "moreno", "brunette"), "dark_brown"),
        (("castana", "castaña", "castano", "castaño"), "brown"),
        (("negra", "negro", "black hair"), "black"),
    ):
        if any(term in normalized for term in terms):
            updates["visual_profile.hair_color"] = {"value": color, "source_text": source_text}
            break

    return updates


def _lab_apply_turn_to_session(session: dict[str, object], message: str) -> None:
    operator_messages = list(session.get("operator_messages", []))
    operator_messages.append(message)
    session["operator_messages"] = operator_messages[-20:]
    manual_overrides = dict(session.get("manual_overrides", {}))
    manual_overrides.update(_lab_extract_turn_updates(message))
    session["manual_overrides"] = manual_overrides
    session["autofill_requested"] = bool(session.get("autofill_requested")) or _lab_autofill_requested(message)


def _lab_eye_color_label(color: object) -> str | None:
    labels = {
        "green": "ojos verdes",
        "blue": "ojos azules",
        "brown": "ojos marrones",
        "hazel": "ojos avellana",
    }
    return labels.get(str(color), str(color) if color else None)


def _lab_hair_color_label(color: object) -> str | None:
    labels = {
        "blonde": "rubia",
        "red": "pelirroja",
        "dark_brown": "morena",
        "brown": "castaña",
        "black": "pelo negro",
    }
    return labels.get(str(color), str(color) if color else None)


def _lab_composed_idea(session: dict[str, object]) -> str:
    messages = [str(item).strip() for item in list(session.get("operator_messages", [])) if str(item).strip()]
    operator_brief = normalize_trace_source_text(" ".join(messages[-6:]), max_length=150, min_length=0) or ""
    manual_overrides = dict(session.get("manual_overrides", {}))
    if not manual_overrides:
        return operator_brief

    parts: list[str] = []
    age_value = manual_overrides.get("identity_core.fictional_age_years", {}).get("value")
    if age_value:
        parts.append(f"modelo de {age_value} años")
    occupation = manual_overrides.get("metadata.occupation_or_content_basis", {}).get("value")
    if occupation:
        parts.append(str(occupation))
    vertical = manual_overrides.get("metadata.vertical", {}).get("value")
    if vertical == "adult_entertainment":
        parts.append("crea contenido NSFW")
    elif vertical:
        parts.append(f"vertical {vertical}")
    scene_context = manual_overrides.get("conversation.scene_context", {}).get("value")
    if scene_context:
        parts.append(str(scene_context))
    speech_style = manual_overrides.get("communication_style.speech_style", {}).get("value")
    if speech_style == "refined":
        parts.append("es formal")
    elif speech_style:
        parts.append(f"speech style {speech_style}")
    eye_color = manual_overrides.get("visual_profile.eye_color", {}).get("value")
    eye_label = _lab_eye_color_label(eye_color)
    if eye_label:
        parts.append(eye_label)
    hair_color = manual_overrides.get("visual_profile.hair_color", {}).get("value")
    hair_label = _lab_hair_color_label(hair_color)
    if hair_label:
        parts.append(hair_label)

    sentence = "Quiero una " + ", ".join(parts) if parts else "Quiero un avatar nuevo"
    if bool(session.get("autofill_requested")) or _LAB_REQUIRED_MANUAL_FIELDS and not _lab_missing_manual_fields(session):
        sentence = f"{sentence}. Completá el resto automáticamente."
    if not operator_brief:
        return sentence
    return (
        normalize_trace_source_text(
            f"{operator_brief}. Atributos consolidados: {sentence}",
            max_length=220,
            min_length=3,
        )
        or sentence
    )


def _lab_missing_manual_fields(session: dict[str, object], state: GraphState | None = None) -> list[str]:
    if bool(session.get("autofill_requested")):
        return []
    manual_overrides = dict(session.get("manual_overrides", {}))
    return [field_path for field_path in _LAB_REQUIRED_MANUAL_FIELDS if field_path not in manual_overrides]


def _lab_chat_readiness_report(session: dict[str, object], state: GraphState | None, *, locale: str | None = None) -> dict[str, object]:
    language = _lab_normalize_locale(locale or session.get("locale"))
    missing_fields = _lab_missing_manual_fields(session, state)
    missing_labels = [_lab_field_label(field_path, locale=language) for field_path in missing_fields]
    next_question = (
        _LAB_MISSING_FIELD_QUESTIONS_BY_LOCALE.get(language, _LAB_MISSING_FIELD_QUESTIONS_BY_LOCALE["en"]).get(missing_fields[0])
        if missing_fields
        else None
    )
    can_handoff = bool(
        state is not None
        and state.completion_status == CompletionStatus.SUCCEEDED
        and not missing_fields
    )
    return {
        "can_handoff": can_handoff,
        "missing_fields": missing_fields,
        "missing_field_labels": missing_labels,
        "next_question": next_question,
        "autofill_available": bool(missing_fields) and not bool(session.get("autofill_requested")),
    }


def _lab_upsert_manual_trace(
    traces: list[dict[str, object]],
    *,
    field_path: str,
    source_text: object,
) -> list[dict[str, object]]:
    normalized_source = normalize_trace_source_text(source_text) or "turno_operador"
    updated = [dict(trace) for trace in traces if trace.get("field_path") != field_path]
    updated.append(
        {
            "field_path": field_path,
            "origin": "manual",
            "source_text": normalized_source,
            "confidence": 1.0,
            "rationale": "Campo manual actualizado desde el turno conversacional mas reciente.",
        }
    )
    return updated


def _lab_overlay_state_with_session(state: GraphState, session: dict[str, object]) -> GraphState:
    manual_overrides = dict(session.get("manual_overrides", {}))
    if not manual_overrides:
        return state

    payload = state.model_dump(mode="json")
    identity_draft = dict(payload.get("identity_draft", {}) or {})
    final_sheet = dict(payload.get("final_technical_sheet_payload", {}) or {})
    normalized_constraints = dict(payload.get("normalized_constraints", {}) or {})
    traces = list(identity_draft.get("field_traces", []) or [])
    sheet_traceability = dict(final_sheet.get("traceability", {}) or {})
    sheet_traces = list(sheet_traceability.get("field_traces", []) or [])

    metadata = dict(identity_draft.get("metadata", {}) or {})
    identity_metadata = dict(final_sheet.get("identity_metadata", {}) or {})
    communication_style = dict(identity_draft.get("communication_style", {}) or {})
    personality_profile = dict(final_sheet.get("personality_profile", {}) or {})
    profile_communication_style = dict(personality_profile.get("communication_style", {}) or {})
    visual_profile = dict(final_sheet.get("visual_profile", {}) or {})
    identity_core = dict(final_sheet.get("identity_core", {}) or {})

    for field_path, update in manual_overrides.items():
        value = update.get("value")
        source_text = update.get("source_text")
        should_trace = True
        if field_path == "identity_core.fictional_age_years":
            identity_core["fictional_age_years"] = value
        elif field_path == "metadata.category":
            metadata["category"] = value
            identity_metadata["category"] = value
            normalized_constraints["category"] = value
        elif field_path == "metadata.vertical":
            metadata["vertical"] = value
            identity_metadata["vertical"] = value
            normalized_constraints["vertical"] = value
        elif field_path == "metadata.occupation_or_content_basis":
            metadata["occupation_or_content_basis"] = value
            identity_metadata["occupation_or_content_basis"] = value
            normalized_constraints["occupation_or_content_basis"] = value
        elif field_path == "voice_tone":
            personality_profile["voice_tone"] = value
            normalized_constraints["voice_tone"] = value
        elif field_path == "communication_style.speech_style":
            communication_style["speech_style"] = value
            profile_communication_style["speech_style"] = value
            normalized_constraints["speech_style"] = value
        elif field_path == "visual_profile.eye_color":
            visual_profile["eye_color"] = value
        elif field_path == "visual_profile.hair_color":
            visual_profile["hair_color"] = value
        elif field_path != "conversation.scene_context":
            should_trace = False
        if should_trace:
            traces = _lab_upsert_manual_trace(traces, field_path=field_path, source_text=source_text)
            sheet_traces = _lab_upsert_manual_trace(sheet_traces, field_path=field_path, source_text=source_text)

    identity_draft["metadata"] = metadata
    identity_draft["communication_style"] = communication_style
    identity_draft["field_traces"] = traces
    final_sheet["identity_metadata"] = identity_metadata
    personality_profile["communication_style"] = profile_communication_style
    final_sheet["personality_profile"] = personality_profile
    final_sheet["visual_profile"] = visual_profile
    final_sheet["identity_core"] = identity_core
    sheet_traceability["field_traces"] = sheet_traces[:40]
    final_sheet["traceability"] = sheet_traceability
    payload["identity_draft"] = identity_draft
    payload["final_technical_sheet_payload"] = final_sheet
    payload["normalized_constraints"] = normalized_constraints

    manual_fields = list(dict.fromkeys([*payload.get("manually_defined_fields", []), *manual_overrides.keys()]))
    inferred_fields = [
        field_path
        for field_path in payload.get("inferred_fields", [])
        if field_path not in manual_overrides
    ]
    payload["manually_defined_fields"] = manual_fields[:24]
    payload["inferred_fields"] = inferred_fields[:24]
    return GraphState.model_validate(payload)


def _lab_store_draft_snapshot(session: dict[str, object], state: GraphState) -> None:
    technical_sheet = state.final_technical_sheet_payload
    if technical_sheet is None:
        return
    session["draft_snapshot"] = {
        "identity": {
            "display_name": technical_sheet.identity_core.display_name,
            "vertical": _enum_or_value(technical_sheet.identity_metadata.vertical),
            "category": _enum_or_value(technical_sheet.identity_metadata.category),
            "style": _enum_or_value(technical_sheet.identity_metadata.style),
            "archetype": _enum_or_value(technical_sheet.personality_profile.archetype),
            "voice_tone": _enum_or_value(technical_sheet.personality_profile.voice_tone),
            "speech_style": _enum_or_value(technical_sheet.personality_profile.communication_style.speech_style),
            "fictional_age_years": technical_sheet.identity_core.fictional_age_years,
            "occupation_or_content_basis": technical_sheet.identity_metadata.occupation_or_content_basis,
        },
        "visual_profile": technical_sheet.visual_profile.model_dump(mode="json"),
        "conversation": {
            "scene_context": dict(session.get("manual_overrides", {})).get("conversation.scene_context", {}).get("value"),
            "autofill_requested": bool(session.get("autofill_requested")),
        },
    }


def _lab_reference_summary(
    session: dict[str, object],
    *,
    fallback_reference_url: str | None = None,
    locale: str | None = None,
) -> dict[str, object]:
    language = _lab_normalize_locale(locale or session.get("locale"))
    uploaded = session.get("uploaded_reference")
    if isinstance(uploaded, dict) and uploaded.get("url"):
        return {
            "source": "file",
            "label": uploaded.get("filename") or "reference upload",
            "effective_url": uploaded.get("url"),
            "filename": uploaded.get("filename"),
            "content_type": uploaded.get("content_type"),
        }
    raw_url = str(fallback_reference_url or session.get("reference_face_image_url") or "").strip()
    if raw_url.startswith("https://example.com/") or raw_url.startswith("http://example.com/"):
        raw_url = ""
    if raw_url:
        return {
            "source": "url",
            "label": raw_url,
            "effective_url": raw_url,
            "filename": None,
            "content_type": None,
        }
    return {
        "source": "none",
        "label": _lab_text(language, "no_reference"),
        "effective_url": None,
        "filename": None,
        "content_type": None,
    }


def _lab_operator_brief(session: dict[str, object], *, locale: str | None = None) -> str:
    language = _lab_normalize_locale(locale or session.get("locale"))
    messages = [str(item).strip() for item in list(session.get("operator_messages", [])) if str(item).strip()]
    if not messages:
        return ""
    if len(messages) == 1:
        return messages[0]
    lines = [_lab_text(language, "operator_context_title")]
    turn_label = _lab_text(language, "turn_label")
    lines.extend(f"- {turn_label} {index}: {message}" for index, message in enumerate(messages, start=1))
    return "\n".join(lines)


def _lab_identity_context(technical_sheet: object, state: GraphState | None = None) -> dict[str, object]:
    context = {
        "identity_summary": technical_sheet.system5_slots.persona_summary,
        "summary": technical_sheet.identity_core.tagline,
        "voice_tone": _enum_or_value(technical_sheet.personality_profile.voice_tone),
        "style": _enum_or_value(technical_sheet.identity_metadata.style),
        "vertical": _enum_or_value(technical_sheet.identity_metadata.vertical),
        "occupation_or_content_basis": technical_sheet.identity_metadata.occupation_or_content_basis,
        "display_name": technical_sheet.identity_core.display_name,
        "archetype": _enum_or_value(technical_sheet.personality_profile.archetype),
        "personality_axes": technical_sheet.personality_profile.axes.model_dump(mode="json"),
        "visual_profile": technical_sheet.visual_profile.model_dump(mode="json"),
        "interests": list(technical_sheet.narrative_profile.interests),
    }
    if state is not None and state.copilot_recommendation is not None:
        context["copilot_workflow_id"] = state.copilot_recommendation.workflow_id
        context["copilot_workflow_family"] = state.copilot_recommendation.recommended_workflow_family
        context["copilot_registry_source"] = state.copilot_recommendation.registry_source
    return context


def _lab_identity_id(state: GraphState) -> str:
    technical_sheet = state.final_technical_sheet_payload
    if technical_sheet is None:
        return uuid.uuid4().hex
    avatar_id = technical_sheet.identity_metadata.avatar_id
    if avatar_id:
        try:
            return str(UUID(str(avatar_id)))
        except ValueError:
            stable_basis = f"vb-lab:{avatar_id}"
    else:
        stable_basis = f"vb-lab:{technical_sheet.identity_core.display_name}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, stable_basis))


def _summarize_visual_profile(visual_profile: dict[str, object]) -> dict[str, object]:
    return {
        "archetype": visual_profile.get("archetype"),
        "hair": " / ".join(
            str(bit) for bit in (visual_profile.get("hair_color"), visual_profile.get("hair_style")) if bit
        ),
        "eyes": visual_profile.get("eye_color"),
        "body_type": visual_profile.get("body_type"),
        "must_haves": visual_profile.get("visual_must_haves", []),
        "wardrobe_styles": visual_profile.get("wardrobe_styles", []),
    }


def _lab_prompt_from_state(state: GraphState) -> str:
    copilot = state.copilot_recommendation
    technical_sheet = state.final_technical_sheet_payload
    if copilot is not None and copilot.prompt_template:
        return copilot.prompt_template
    if technical_sheet is None:
        return "Photorealistic identity portrait with premium editorial realism."
    return (
        f"Photorealistic portrait of {technical_sheet.identity_core.display_name}, "
        f"{_enum_or_value(technical_sheet.identity_metadata.style)} style, "
        f"{_enum_or_value(technical_sheet.identity_metadata.vertical)} vertical, "
        f"{_enum_or_value(technical_sheet.personality_profile.archetype)} archetype."
    )


def _lab_negative_prompt_from_state(state: GraphState) -> str:
    copilot = state.copilot_recommendation
    if copilot is not None and copilot.negative_prompt:
        return copilot.negative_prompt
    return "low quality, anatomy drift, extra limbs, text, watermark, illustration, anime, minors"


def _lab_s1_job_input(state: GraphState, *, reference_face_image_url: str | None = None) -> dict[str, object]:
    technical_sheet = state.final_technical_sheet_payload
    if technical_sheet is None:
        raise ValueError("GraphState must include final_technical_sheet_payload before S1 handoff")
    identity_context = _lab_identity_context(technical_sheet, state)
    copilot = state.copilot_recommendation
    identity_id = _lab_identity_id(state)
    reference_url = (reference_face_image_url or "").strip()
    if reference_url.startswith("https://example.com/") or reference_url.startswith("http://example.com/"):
        reference_url = ""
    ip_adapter_enabled = bool(reference_url)
    return {
        "action": "generate",
        "mode": "base_render",
        "workflow_id": copilot.workflow_id if copilot is not None else COMFYUI_WORKFLOW_IMAGE_ID,
        "workflow_version": copilot.workflow_version if copilot is not None else COMFYUI_WORKFLOW_IMAGE_VERSION,
        "workflow_family": (
            copilot.recommended_workflow_family if copilot is not None else "flux_identity_reference"
        ),
        "workflow_registry_source": copilot.registry_source if copilot is not None else "approved_internal",
        "base_model_id": copilot.base_model_id if copilot is not None else "flux-schnell-v1",
        "runtime_stage": RuntimeStage.IDENTITY_IMAGE.value,
        "prompt": _lab_prompt_from_state(state),
        "negative_prompt": _lab_negative_prompt_from_state(state),
        "seed": 42,
        "width": 1024,
        "height": 1024,
        "reference_face_image_url": reference_url or None,
        "ip_adapter": {"enabled": ip_adapter_enabled, "model_name": "plus_face", "weight": 0.9},
        "face_detailer": {"enabled": True, "confidence_threshold": 0.8, "inpaint_strength": 0.35},
        "realism_profile": "photorealistic_adult_reference_v1",
        "source_strategy": "copilot_workflow_plus_shot_plan_v2",
        "copilot_prompt_template": copilot.prompt_template if copilot is not None else None,
        "copilot_negative_prompt": copilot.negative_prompt if copilot is not None else None,
        "metadata": {
            "identity_id": identity_id,
            "character_id": identity_id,
            "autopromote": False,
            "samples_target": 40,
            "identity_context": identity_context,
            "source_mode": "langgraph_lab",
        },
    }


def _lab_panel_changes(
    previous_panel: dict[str, object] | None,
    current_panel: dict[str, object],
    *,
    locale: str | None = None,
) -> list[str]:
    if not previous_panel:
        return []
    language = _lab_normalize_locale(locale)
    change_labels = {
        "en": {
            "display_name": "name",
            "vertical": "content type",
            "category": "category",
            "style": "style",
            "archetype": "archetype",
            "voice_tone": "voice tone",
            "speech_style": "speech",
        },
        "es": {
            "display_name": "nombre",
            "vertical": "tipo de contenido",
            "category": "categoria",
            "style": "estilo",
            "archetype": "arquetipo",
            "voice_tone": "tono",
            "speech_style": "habla",
        },
    }
    changes: list[str] = []
    current_identity = current_panel.get("identity", {})
    previous_identity = previous_panel.get("identity", {})
    for key in ("display_name", "vertical", "category", "style", "archetype", "voice_tone", "speech_style"):
        current_value = current_identity.get(key) if isinstance(current_identity, dict) else None
        previous_value = previous_identity.get(key) if isinstance(previous_identity, dict) else None
        if current_value and current_value != previous_value:
            label = change_labels.get(language, change_labels["en"]).get(key, key)
            changes.append(f"{label}: {current_value}")
    return changes[:4]


def _lab_assistant_message(
    state: GraphState,
    panel: dict[str, object],
    *,
    previous_panel: dict[str, object] | None = None,
    locale: str | None = None,
) -> str:
    language = _lab_normalize_locale(locale)
    if state.completion_status == CompletionStatus.FAILED:
        return _lab_text(language, "failed_turn")
    changes = _lab_panel_changes(previous_panel, panel, locale=language)
    readiness = dict(panel.get("readiness", {}) or {})
    missing_fields = list(readiness.get("missing_fields") or [])
    missing_labels = list(readiness.get("missing_field_labels") or [])
    next_question = readiness.get("next_question")
    autofill_available = bool(readiness.get("autofill_available"))
    display_name = (panel.get("identity") or {}).get("display_name") or _lab_text(language, "avatar_fallback")
    prefix = _lab_text(language, "draft_created") if previous_panel is None else _lab_text(
        language,
        "draft_updated",
        display_name=display_name,
    )
    details = _lab_text(language, "detected_changes", changes=", ".join(changes)) if changes else ""
    if missing_fields:
        labels = missing_labels or [_lab_field_label(field_path, locale=language) for field_path in missing_fields]
        guidance = f" {next_question}" if next_question else ""
        if autofill_available:
            guidance = f"{guidance}{_lab_text(language, 'autofill_hint')}".rstrip()
        return f"{prefix}{details}{_lab_text(language, 'not_ready', missing=', '.join(labels[:4]))}{guidance}"
    return f"{prefix}{details}{_lab_text(language, 'ready')}"


def _lab_state_summary(
    state: GraphState,
    *,
    reference_summary: dict[str, object] | None = None,
    conversation_summary: dict[str, object] | None = None,
    readiness_report: dict[str, object] | None = None,
) -> dict[str, object]:
    technical_sheet = state.final_technical_sheet_payload
    draft = state.identity_draft
    copilot = state.copilot_recommendation
    identity_context = _lab_identity_context(technical_sheet, state) if technical_sheet is not None else {}
    traces = draft.trace_map() if draft is not None else {}
    current_reference = reference_summary or _lab_reference_summary({})
    preview_payload = _lab_s1_job_input(state, reference_face_image_url=current_reference.get("effective_url"))
    readiness = readiness_report or {"can_handoff": False, "missing_fields": [], "next_question": None, "autofill_available": False}
    return {
        "completion_status": _enum_or_value(state.completion_status),
        "identity": {
            "display_name": technical_sheet.identity_core.display_name if technical_sheet is not None else None,
            "vertical": _enum_or_value(technical_sheet.identity_metadata.vertical) if technical_sheet is not None else None,
            "category": _enum_or_value(technical_sheet.identity_metadata.category) if technical_sheet is not None else None,
            "style": _enum_or_value(technical_sheet.identity_metadata.style) if technical_sheet is not None else None,
            "archetype": _enum_or_value(technical_sheet.personality_profile.archetype) if technical_sheet is not None else None,
            "voice_tone": _enum_or_value(technical_sheet.personality_profile.voice_tone) if technical_sheet is not None else None,
            "speech_style": (
                _enum_or_value(technical_sheet.personality_profile.communication_style.speech_style)
                if technical_sheet is not None
                else None
            ),
        },
        "personality_axes": draft.personality_axes.model_dump(mode="json") if draft is not None else {},
        "visual_profile": _summarize_visual_profile(technical_sheet.visual_profile.model_dump(mode="json"))
        if technical_sheet is not None
        else {},
        "traceability": {
            "manual_fields": state.manually_defined_fields,
            "inferred_fields": state.inferred_fields,
            "missing_fields": list(readiness.get("missing_fields") or []),
            "missing_field_labels": list(readiness.get("missing_field_labels") or []),
            "field_traces": {field_path: trace.model_dump(mode="json") for field_path, trace in traces.items()},
        },
        "copilot": (
            {
                "workflow_id": copilot.workflow_id,
                "workflow_version": copilot.workflow_version,
                "base_model_id": copilot.base_model_id,
                "workflow_family": copilot.recommended_workflow_family,
                "registry_source": copilot.registry_source,
                "prompt_template": copilot.prompt_template,
                "negative_prompt": copilot.negative_prompt,
                "reasoning_summary": copilot.reasoning_summary,
                "risk_flags": copilot.risk_flags,
            }
            if copilot is not None
            else {}
        ),
        "identity_context": identity_context,
        "readiness": {
            "can_handoff": bool(readiness.get("can_handoff")),
            "missing_fields": list(readiness.get("missing_fields") or []),
            "missing_field_labels": list(readiness.get("missing_field_labels") or []),
            "next_question": readiness.get("next_question"),
            "autofill_available": bool(readiness.get("autofill_available")),
        },
        "reference_face": current_reference,
        "conversation": conversation_summary or {},
        "s1_payload_preview": preview_payload,
        "graph_state_json": state.model_dump(mode="json"),
    }


def _lab_response_from_state(
    session_id: str,
    message: str,
    state: GraphState,
    *,
    session: dict[str, object],
    previous_panel: dict[str, object] | None = None,
    locale: str | None = None,
) -> dict[str, object]:
    language = _lab_normalize_locale(locale or session.get("locale"))
    readiness = _lab_chat_readiness_report(session, state, locale=language)
    reference_summary = _lab_reference_summary(session, locale=language)
    conversation_summary = {
        "turn_count": len(list(session.get("operator_messages", []))),
        "operator_brief": _lab_operator_brief(session, locale=language),
        "autofill_requested": bool(session.get("autofill_requested")),
    }
    panel = _lab_state_summary(
        state,
        reference_summary=reference_summary,
        conversation_summary=conversation_summary,
        readiness_report=readiness,
    )
    return {
        "session_id": session_id,
        "chat_entry": {
            "user_message": message,
            "assistant_message": _lab_assistant_message(state, panel, previous_panel=previous_panel, locale=language),
            "status": _enum_or_value(state.completion_status),
            "error": state.terminal_error_message,
        },
        "panel": panel,
        "can_handoff": bool(readiness.get("can_handoff")),
        "history": list(session.get("history", [])),
    }


def _lab_error_response(
    session_id: str,
    message_text: str,
    message: str,
    *,
    session: dict[str, object],
    locale: str | None = None,
) -> dict[str, object]:
    language = _lab_normalize_locale(locale or session.get("locale"))
    return {
        "session_id": session_id,
        "chat_entry": {
            "user_message": message_text,
            "assistant_message": _lab_text(language, "failed_conversational_turn"),
            "status": CompletionStatus.FAILED.value,
            "error": message,
        },
        "panel": {
            "completion_status": CompletionStatus.FAILED.value,
            "identity": {},
            "personality_axes": {},
            "visual_profile": {},
            "traceability": {"manual_fields": [], "inferred_fields": [], "missing_fields": [], "field_traces": {}},
            "copilot": {},
            "identity_context": {},
            "readiness": {"can_handoff": False, "missing_fields": []},
            "reference_face": _lab_reference_summary(session, locale=language),
            "conversation": {
                "turn_count": len(list(session.get("operator_messages", []))),
                "operator_brief": _lab_operator_brief(session, locale=language),
            },
            "s1_payload_preview": {},
            "graph_state_json": {},
        },
        "can_handoff": False,
        "history": list(session.get("history", [])),
    }


def _lab_run_chat_turn(
    session_id: str,
    message: str,
    *,
    reference_face_image_url: str | None = None,
    locale: str | None = None,
) -> dict[str, object]:
    session = _lab_session_store(session_id)
    language = _lab_normalize_locale(locale or session.get("locale"))
    session["locale"] = language
    session.setdefault("history", [])
    session.setdefault("operator_messages", [])
    session.setdefault("manual_overrides", {})
    session.setdefault("draft_snapshot", {})
    session.setdefault("autofill_requested", False)
    if reference_face_image_url is not None:
        normalized_reference = reference_face_image_url.strip()
        session["reference_face_image_url"] = normalized_reference
        if not normalized_reference:
            session.pop("reference_face_image_url", None)
    previous_response = session.get("last_response")
    previous_panel = previous_response.get("panel") if isinstance(previous_response, dict) else None
    _lab_apply_turn_to_session(session, message)
    composed_idea = _lab_composed_idea(session)
    try:
        state = _lab_overlay_state_with_session(run_agentic_brain(composed_idea), session)
    except Exception as exc:
        response = _lab_error_response(session_id, message, str(exc), session=session, locale=language)
        history = list(session.get("history", []))
        history.append(response["chat_entry"])
        session["history"] = history[-20:]
        response["history"] = list(session["history"])
        session["last_response"] = response
        return response
    response = _lab_response_from_state(
        session_id,
        message,
        state,
        session=session,
        previous_panel=previous_panel,
        locale=language,
    )
    _lab_store_draft_snapshot(session, state)
    session["last_graph_state"] = state.model_dump(mode="json")
    session["last_readiness"] = dict(response["panel"].get("readiness", {}))
    history = list(session.get("history", []))
    history.append(response["chat_entry"])
    session["history"] = history[-20:]
    response["history"] = list(session["history"])
    session["last_response"] = response
    return response


def _lab_html(*, authenticated: bool, route_mode: str, user: dict[str, object] | None = None) -> str:
    index_file = WEB_PUBLIC_ROOT / "index.html"
    if not index_file.exists():
        raise RuntimeError(f"web app entrypoint is missing at {index_file}")
    config = {
        "authenticated": authenticated,
        "routeMode": route_mode,
        "user": user or {},
        "defaultReferenceFaceImageUrl": "",
        "chatEndpoint": "/lab/chat",
        "langgraphEndpoint": "/lab/langgraph",
        "handoffEndpoint": "/lab/s1-image",
        "loginEndpoint": "/auth/login",
        "logoutEndpoint": "/auth/logout",
        "sessionEndpoint": "/auth/session",
        "referenceUploadEndpoint": "/lab/reference-uploads",
        "sessionStorageKey": "vb-web-session",
    }
    template = index_file.read_text(encoding="utf-8")
    return template.replace("__VB_WEB_CONFIG__", json.dumps(config, ensure_ascii=False))


def _web_asset_path(asset_path: str) -> Path:
    candidate = (WEB_ASSETS_ROOT / asset_path).resolve()
    if WEB_ASSETS_ROOT.resolve() not in candidate.parents and candidate != WEB_ASSETS_ROOT.resolve():
        raise HTTPException(status_code=404, detail="asset not found")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="asset not found")
    return candidate


runtime = InMemoryServiceRuntime(processor=_processor)
app = FastAPI(title="VixenBliss S1 Image Runtime", version="1.0.0")

try:
    _directus_recorder = S1RuntimeDirectusRecorder.from_settings(S1ControlSettings.from_env())
except Exception:
    _directus_recorder = None


def _record_directus_run(record: object, job_input: dict) -> None:
    if _directus_recorder is None:
        return
    try:
        run = _directus_recorder.record_job(
            service_name="s1_image",
            job_id=record.job_id,
            status=record.status.value,
            input_payload=job_input,
            result_payload=record.result,
            error_message=record.error_message,
        )
        if record.result is not None and isinstance(run, dict):
            record.result.setdefault("metadata", {})
            record.result["metadata"]["directus_run_id"] = str(run.get("id"))
    except Exception as exc:
        if record.result is not None:
            record.result.setdefault("metadata", {})
            record.result["metadata"]["directus_recording_failed"] = True
            record.result["metadata"]["directus_recording_error"] = str(exc)


@app.get("/lab", response_class=HTMLResponse)
def langgraph_lab(request: Request) -> Response:
    session = _active_auth_session(request)
    if session is None:
        return RedirectResponse(url="/login", status_code=303)
    return HTMLResponse(_lab_html(authenticated=True, route_mode="app", user=_auth_identity(session)))


@app.get("/", response_class=HTMLResponse)
def web_home(request: Request) -> Response:
    session = _active_auth_session(request)
    if session is None:
        return RedirectResponse(url="/login", status_code=303)
    return HTMLResponse(_lab_html(authenticated=True, route_mode="app", user=_auth_identity(session)))


@app.get("/app", response_class=HTMLResponse)
def web_app(request: Request) -> Response:
    session = _active_auth_session(request)
    if session is None:
        return RedirectResponse(url="/login", status_code=303)
    return HTMLResponse(_lab_html(authenticated=True, route_mode="app", user=_auth_identity(session)))


@app.get("/login", response_class=HTMLResponse)
def web_login(request: Request) -> Response:
    session = _active_auth_session(request)
    if session is not None:
        return RedirectResponse(url="/app", status_code=303)
    return HTMLResponse(_lab_html(authenticated=False, route_mode="login"))


@app.get("/auth/session")
def auth_session(request: Request) -> dict[str, object]:
    session = _active_auth_session(request)
    if session is None:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": _auth_identity(session)}


@app.post("/auth/login")
def auth_login(payload: dict, response: Response) -> dict[str, object]:
    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", "")).strip()
    if not email or not password:
        raise HTTPException(status_code=422, detail="email and password are required")
    try:
        auth_payload = _directus_login(email, password)
        user_payload = _directus_me(str(auth_payload["access_token"]))
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Directus login failed: {exc}") from exc
    session_id, auth_session_payload = _create_auth_session(user_payload, auth_payload)
    _set_auth_cookie(response, session_id)
    return {"authenticated": True, "user": _auth_identity(auth_session_payload)}


@app.post("/auth/logout")
def auth_logout(request: Request, response: Response) -> dict[str, object]:
    session = _active_auth_session(request)
    if session is not None:
        _WEB_AUTH_SESSIONS.pop(str(session.get("session_id")), None)
    _clear_auth_cookie(response)
    return {"authenticated": False}


@app.get("/web/assets/{asset_path:path}")
def web_asset(asset_path: str) -> FileResponse:
    return FileResponse(_web_asset_path(asset_path))


@app.get("/lab/reference-files/{reference_id}")
def lab_reference_file(reference_id: str, request: Request) -> FileResponse:
    _require_auth(request)
    payload = _LAB_REFERENCE_UPLOADS.get(reference_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="reference file not found")
    file_path = Path(str(payload["path"]))
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="reference file not found")
    return FileResponse(file_path, media_type=str(payload.get("content_type") or "application/octet-stream"))


@app.post("/lab/reference-uploads")
def upload_lab_reference(payload: dict, request: Request) -> dict[str, object]:
    _require_auth(request)
    session_id = str(payload.get("session_id", "")).strip()
    locale = _lab_normalize_locale(payload.get("locale"))
    file_name = str(payload.get("filename", "")).strip()
    content_type = str(payload.get("content_type", "")).strip() or "application/octet-stream"
    inline_data = str(payload.get("data_base64", "")).strip()
    if not session_id or not file_name or not inline_data:
        raise HTTPException(status_code=422, detail="session_id, filename and data_base64 are required")
    try:
        file_bytes = base64.b64decode(inline_data, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"invalid reference upload payload: {exc}") from exc
    extension = Path(file_name).suffix or ".bin"
    reference_id = uuid.uuid4().hex
    target_path = LAB_REFERENCE_UPLOAD_ROOT / f"{reference_id}{extension}"
    target_path.write_bytes(file_bytes)
    public_url = str(request.base_url).rstrip("/") + f"/lab/reference-files/{reference_id}"
    reference_payload = {
        "id": reference_id,
        "filename": file_name,
        "content_type": content_type,
        "path": str(target_path),
        "url": public_url,
    }
    _LAB_REFERENCE_UPLOADS[reference_id] = reference_payload
    session = _lab_session_store(session_id)
    session["locale"] = locale
    session["uploaded_reference"] = reference_payload
    return {"reference": _lab_reference_summary(session, locale=locale)}


@app.post("/lab/chat")
def run_langgraph_chat(payload: dict, request: Request) -> dict:
    _require_auth(request)
    message = str(payload.get("message", "")).strip()
    session_id = str(payload.get("session_id", "")).strip() or f"lab-{uuid.uuid4().hex}"
    locale = _lab_normalize_locale(payload.get("locale"))
    if not message:
        raise HTTPException(status_code=422, detail="message is required")
    reference_face_image_url = str(payload.get("reference_face_image_url", "")).strip()
    return _lab_run_chat_turn(
        session_id,
        message,
        reference_face_image_url=reference_face_image_url if reference_face_image_url else None,
        locale=locale,
    )


@app.post("/lab/langgraph")
def run_langgraph_lab(payload: dict, request: Request) -> dict:
    _require_auth(request)
    idea = str(payload.get("idea", "")).strip()
    session_id = str(payload.get("session_id", "")).strip() or f"lab-{uuid.uuid4().hex}"
    locale = _lab_normalize_locale(payload.get("locale"))
    if not idea:
        raise HTTPException(status_code=422, detail="idea is required")
    reference_face_image_url = str(payload.get("reference_face_image_url", "")).strip()
    return _lab_run_chat_turn(
        session_id,
        idea,
        reference_face_image_url=reference_face_image_url if reference_face_image_url else None,
        locale=locale,
    )


@app.post("/lab/s1-image")
def handoff_langgraph_lab_to_s1(payload: dict, request: Request) -> dict:
    _require_auth(request)
    session_id = str(payload.get("session_id", "")).strip()
    locale = _lab_normalize_locale(payload.get("locale"))
    if not session_id:
        raise HTTPException(status_code=422, detail="session_id is required")
    session = _LAB_SESSIONS.get(session_id)
    if not session or "last_graph_state" not in session:
        raise HTTPException(status_code=409, detail=_lab_text(locale, "no_previous_run"))
    state = GraphState.model_validate(session["last_graph_state"])
    session["locale"] = locale
    readiness = _lab_chat_readiness_report(session, state, locale=locale)
    if state.completion_status != CompletionStatus.SUCCEEDED:
        raise HTTPException(status_code=409, detail=_lab_text(locale, "graph_not_ready"))
    if not readiness["can_handoff"]:
        missing = ", ".join(readiness["missing_field_labels"] or readiness["missing_fields"])
        raise HTTPException(
            status_code=409,
            detail=_lab_text(locale, "handoff_not_ready", missing=missing),
        )
    reference_face_image_url = str(payload.get("reference_face_image_url", "")).strip() or None
    reference_summary = _lab_reference_summary(session, fallback_reference_url=reference_face_image_url, locale=locale)
    job_input = _lab_s1_job_input(state, reference_face_image_url=reference_summary.get("effective_url"))
    job_response = submit_job({"input": job_input})
    panel = _lab_state_summary(
        state,
        reference_summary=reference_summary,
        conversation_summary={
            "turn_count": len(list(session.get("operator_messages", []))),
            "operator_brief": _lab_operator_brief(session, locale=locale),
            "autofill_requested": bool(session.get("autofill_requested")),
        },
        readiness_report=readiness,
    )
    panel["s1_payload_preview"] = job_input
    response = {
        "session_id": session_id,
        "panel": panel,
        "handoff": {
            "reference_face_image_url": job_input.get("reference_face_image_url"),
            "reference_face_source": reference_summary.get("source"),
            "job": job_response,
        },
    }
    session["last_handoff"] = response["handoff"]
    return response


@app.get("/healthcheck")
def healthcheck(deep: bool = False) -> dict:
    if S1_IMAGE_EXECUTION_BACKEND == "modal":
        try:
            import modal
        except Exception as exc:
            return {
                "ok": False,
                "provider_ready": False,
                "service": "s1_image",
                "provider": Provider.MODAL.value,
                "progress_transport": "websocket_optional",
                "startup_mode": "remote_gpu_worker",
                "deep_healthcheck": deep,
                "comfyui_reachable": False,
                "workflow_id": COMFYUI_WORKFLOW_IMAGE_ID,
                "workflow_version": COMFYUI_WORKFLOW_IMAGE_VERSION,
                "ip_adapter_model": COMFYUI_IP_ADAPTER_MODEL,
                "runtime_checks": {},
                "runtime_contract": {
                    "model_family": "flux",
                    "runtime_stage": RuntimeStage.IDENTITY_IMAGE.value,
                    "workflow_scope": "s1_image",
                    "supabase_required": False,
                    "reference_face_image_url_required": False,
                    "lora_supported": False,
                    "model_cache_root": str(MODEL_CACHE_ROOT),
                },
                "startup_error": f"modal backend is not available in this runtime ({exc})",
            }

        modal_function = modal.Function.from_name(S1_IMAGE_MODAL_APP_NAME, S1_IMAGE_MODAL_HEALTHCHECK_FUNCTION_NAME)
        payload = modal_function.remote(deep=deep)
        payload["startup_mode"] = "remote_gpu_worker"
        payload["orchestrator_host"] = "coolify"
        payload["gpu_worker_provider"] = Provider.MODAL.value
        return payload

    runtime_checks = _runtime_checks({})
    asset_ready = _runtime_assets_ready(runtime_checks, allow_cache_only=True)
    provider_ready = asset_ready
    startup_error = None
    comfyui_reachable = _healthcheck()
    provider_ready = provider_ready or comfyui_reachable
    try:
        if deep:
            _ensure_comfyui_running()
            runtime_checks = _runtime_checks({})
            asset_ready = _runtime_assets_ready(runtime_checks, allow_cache_only=False)
            comfyui_reachable = _healthcheck()
            provider_ready = (asset_ready or comfyui_reachable) and comfyui_reachable
    except Exception as exc:
        startup_error = str(exc)
        provider_ready = False
    return {
        "ok": provider_ready,
        "provider_ready": provider_ready,
        "service": "s1_image",
        "provider": Provider.MODAL.value,
        "progress_transport": "websocket_optional",
        "startup_mode": "lazy",
        "deep_healthcheck": deep,
        "comfyui_reachable": comfyui_reachable,
        "workflow_id": COMFYUI_WORKFLOW_IMAGE_ID,
        "workflow_version": COMFYUI_WORKFLOW_IMAGE_VERSION,
        "ip_adapter_model": COMFYUI_IP_ADAPTER_MODEL,
        "runtime_checks": runtime_checks,
        "runtime_contract": {
            "model_family": "flux",
            "runtime_stage": RuntimeStage.IDENTITY_IMAGE.value,
            "workflow_scope": "s1_image",
            "supabase_required": False,
            "reference_face_image_url_required": False,
            "lora_supported": False,
            "model_cache_root": str(MODEL_CACHE_ROOT),
        },
        "startup_error": startup_error,
    }


@app.post("/jobs")
def submit_job(payload: dict) -> dict:
    job_input = payload.get("input", payload)
    record = runtime.submit(job_input)
    _record_directus_run(record, job_input)
    response = record.status_payload(
        progress_url=f"/ws/jobs/{record.job_id}",
        result_url=f"/jobs/{record.job_id}/result",
    )
    if record.result is not None:
        response["output"] = record.result
    return response


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
        sent = 0
        while True:
            record = runtime.status(job_id)
            pending_events = record.progress_events[sent:]
            for event in pending_events:
                await websocket.send_json(event.model_dump(mode="json"))
                sent += 1
            if record.status.value in {"completed", "failed"}:
                break
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        return
    await websocket.close()
