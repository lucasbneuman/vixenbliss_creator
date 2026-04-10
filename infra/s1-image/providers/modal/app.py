from __future__ import annotations

import importlib.util
import os
import shutil
from pathlib import Path

import modal


APP_NAME = os.getenv("S1_IMAGE_MODAL_APP_NAME", "vixenbliss-s1-image")
MODEL_CACHE_ROOT = "/cache/models"
CLIP_VISION_MODEL = os.getenv("COMFYUI_IP_ADAPTER_CLIP_VISION_MODEL", "google/siglip-so400m-patch14-384")
CLIP_VISION_DIRNAME = CLIP_VISION_MODEL.split("/")[-1]
FACE_DETECTOR_MODEL = os.getenv("COMFYUI_FACE_DETECTOR_MODEL", "face_yolov8m.pt")

app = modal.App(APP_NAME)

directus_secret = modal.Secret.from_name("vixenbliss-s1-control-plane")
model_cache_volume = modal.Volume.from_name("vixenbliss-s1-image-model-cache", create_if_missing=True)
hf_token = os.getenv("HF_TOKEN", "").strip()
hf_secret = modal.Secret.from_dict({"HF_TOKEN": hf_token}) if hf_token else None
function_secrets = [directus_secret]
if hf_secret is not None:
    function_secrets.append(hf_secret)

image = (
    modal.Image.from_dockerfile(
        "infra/s1-image/runtime/Dockerfile",
        context_dir=".",
        force_build=True,
    )
    .env(
        {
            "PYTHONPATH": "/app/src",
            "RUNTIME_ROOT": "/app/runtime",
            "SERVICE_ARTIFACT_ROOT": "/app/data/artifacts",
            "COMFYUI_HOME": "/opt/comfyui",
            "COMFYUI_CUSTOM_NODES_DIR": "/opt/comfyui/custom_nodes",
            "COMFYUI_MODELS_DIR": "/opt/comfyui/models",
            "COMFYUI_USER_DIR": "/opt/comfyui/user/default",
            "COMFYUI_INPUT_DIR": "/opt/comfyui/input",
            "COMFYUI_PORT": "8188",
            "COMFYUI_BASE_URL": "http://127.0.0.1:8188",
            "MODEL_CACHE_ROOT": "/cache/models",
            "S1_IMAGE_EXECUTION_BACKEND": "local",
            "COMFYUI_WORKFLOW_IDENTITY_ID": os.getenv("COMFYUI_WORKFLOW_IDENTITY_ID", "lora-dataset-ipadapter-batch"),
            "COMFYUI_WORKFLOW_IDENTITY_VERSION": os.getenv("COMFYUI_WORKFLOW_IDENTITY_VERSION", "2026-04-08"),
            "COMFYUI_IP_ADAPTER_MODEL": os.getenv("COMFYUI_IP_ADAPTER_MODEL", "plus_face"),
            "COMFYUI_FACE_CONFIDENCE_THRESHOLD": os.getenv("COMFYUI_FACE_CONFIDENCE_THRESHOLD", "0.8"),
            "COMFYUI_FLUX_DIFFUSION_MODEL_NAME": os.getenv("COMFYUI_FLUX_DIFFUSION_MODEL_NAME", "flux1-schnell.safetensors"),
            "COMFYUI_FLUX_AE_NAME": os.getenv("COMFYUI_FLUX_AE_NAME", "ae.safetensors"),
            "COMFYUI_FLUX_CLIP_L_NAME": os.getenv("COMFYUI_FLUX_CLIP_L_NAME", "clip_l.safetensors"),
            "COMFYUI_FLUX_T5XXL_NAME": os.getenv("COMFYUI_FLUX_T5XXL_NAME", "t5xxl_fp8_e4m3fn.safetensors"),
            "DEFAULT_RENDER_SAMPLES_TARGET": os.getenv("DEFAULT_RENDER_SAMPLES_TARGET", "80"),
            "DEFAULT_TRAINING_SAMPLES_TARGET": os.getenv("DEFAULT_TRAINING_SAMPLES_TARGET", "40"),
            "DEFAULT_SELECTION_POLICY": os.getenv("DEFAULT_SELECTION_POLICY", "score_curated_v1"),
        }
    )
)


@app.function(
    image=image,
    gpu="A10G",
    timeout=3600,
    scaledown_window=90,
    volumes={"/cache/models": model_cache_volume},
    secrets=function_secrets,
)
def run_s1_image_job(payload: dict) -> dict:
    spec = importlib.util.spec_from_file_location("vixenbliss_s1_image_runtime", "/app/runtime/app.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    progress_events: list[dict[str, object]] = []

    def emit_progress(stage: str, message: str, progress: float) -> None:
        progress_events.append({"stage": stage, "message": message, "progress": progress})

    result = module._processor(payload, emit_progress=emit_progress)
    metadata = result.setdefault("metadata", {})
    metadata["modal_progress_events"] = progress_events
    return result


@app.function(
    image=image,
    gpu="A10G",
    timeout=300,
    scaledown_window=90,
    volumes={"/cache/models": model_cache_volume},
    secrets=function_secrets,
)
def runtime_healthcheck(deep: bool = False) -> dict:
    spec = importlib.util.spec_from_file_location("vixenbliss_s1_image_runtime", "/app/runtime/app.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.healthcheck(deep=deep)


def _download_model(repo_id: str, filename: str, target: Path, *, token: str | None, gated: bool) -> None:
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import GatedRepoError, HfHubHTTPError

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    if gated and not token:
        raise RuntimeError(f"HF_TOKEN is required to download gated model {repo_id}/{filename}")
    try:
        cached = Path(
            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                token=token,
            )
        )
    except GatedRepoError as exc:
        raise RuntimeError(f"Access denied to gated repo {repo_id}. Accept the model terms and use a valid HF_TOKEN.") from exc
    except HfHubHTTPError as exc:
        raise RuntimeError(f"Failed downloading {repo_id}/{filename}: {exc}") from exc
    shutil.copyfile(cached, target)


def _download_repo_snapshot(repo_id: str, target_dir: Path, *, token: str | None) -> None:
    from huggingface_hub import snapshot_download

    if target_dir.exists() and any(target_dir.iterdir()):
        return
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=repo_id,
        token=token,
        local_dir=target_dir,
        local_dir_use_symlinks=False,
    )


@app.function(
    image=image,
    timeout=3600,
    volumes={"/cache/models": model_cache_volume},
    secrets=function_secrets,
)
def prime_model_cache() -> dict:
    cache_root = Path(MODEL_CACHE_ROOT)
    token = os.getenv("HF_TOKEN")

    downloads = [
        (
            os.getenv("FLUX_REPO_ID", "black-forest-labs/FLUX.1-schnell"),
            os.getenv("COMFYUI_FLUX_DIFFUSION_MODEL_NAME", "flux1-schnell.safetensors"),
            cache_root / "diffusion_models" / os.getenv("COMFYUI_FLUX_DIFFUSION_MODEL_NAME", "flux1-schnell.safetensors"),
            True,
        ),
        (
            os.getenv("FLUX_REPO_ID", "black-forest-labs/FLUX.1-schnell"),
            os.getenv("COMFYUI_FLUX_AE_NAME", "ae.safetensors"),
            cache_root / "vae" / os.getenv("COMFYUI_FLUX_AE_NAME", "ae.safetensors"),
            True,
        ),
        (
            os.getenv("FLUX_TEXT_ENCODERS_REPO_ID", "comfyanonymous/flux_text_encoders"),
            os.getenv("COMFYUI_FLUX_CLIP_L_NAME", "clip_l.safetensors"),
            cache_root / "text_encoders" / os.getenv("COMFYUI_FLUX_CLIP_L_NAME", "clip_l.safetensors"),
            False,
        ),
        (
            os.getenv("FLUX_TEXT_ENCODERS_REPO_ID", "comfyanonymous/flux_text_encoders"),
            os.getenv("COMFYUI_FLUX_T5XXL_NAME", "t5xxl_fp8_e4m3fn.safetensors"),
            cache_root / "text_encoders" / os.getenv("COMFYUI_FLUX_T5XXL_NAME", "t5xxl_fp8_e4m3fn.safetensors"),
            False,
        ),
        (
            os.getenv("FLUX_IPADAPTER_REPO_ID", "InstantX/FLUX.1-dev-IP-Adapter"),
            os.getenv("FLUX_IPADAPTER_SOURCE_FILENAME", "ip-adapter.bin"),
            cache_root / "ipadapter-flux" / "ip-adapter.bin",
            False,
        ),
        (
            os.getenv("COMFYUI_FACE_DETECTOR_REPO_ID", "Bingsu/adetailer"),
            FACE_DETECTOR_MODEL,
            cache_root / "ultralytics" / "bbox" / FACE_DETECTOR_MODEL,
            False,
        ),
    ]

    for repo_id, filename, target, gated in downloads:
        _download_model(repo_id, filename, target, token=token, gated=gated)

    clip_vision_target = cache_root / "clip_vision" / CLIP_VISION_DIRNAME
    _download_repo_snapshot(CLIP_VISION_MODEL, clip_vision_target, token=token)

    model_cache_volume.commit()
    return {
        "ok": True,
        "model_cache_root": MODEL_CACHE_ROOT,
        "downloaded_files": [str(target) for _, _, target, _ in downloads],
        "clip_vision_model": CLIP_VISION_MODEL,
        "clip_vision_dir": str(clip_vision_target),
    }
