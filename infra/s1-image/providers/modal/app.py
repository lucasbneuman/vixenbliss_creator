from __future__ import annotations

import importlib.util
import os

import modal


APP_NAME = os.getenv("S1_IMAGE_MODAL_APP_NAME", "vixenbliss-s1-image")

app = modal.App(APP_NAME)

directus_secret = modal.Secret.from_name("vixenbliss-s1-control-plane")
model_cache_volume = modal.Volume.from_name("vixenbliss-s1-image-model-cache", create_if_missing=True)

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
            "COMFYUI_WORKFLOW_IDENTITY_ID": os.getenv("COMFYUI_WORKFLOW_IDENTITY_ID", "base-image-ipadapter-impact"),
            "COMFYUI_WORKFLOW_IDENTITY_VERSION": os.getenv("COMFYUI_WORKFLOW_IDENTITY_VERSION", "2026-03-31"),
            "COMFYUI_IP_ADAPTER_MODEL": os.getenv("COMFYUI_IP_ADAPTER_MODEL", "plus_face"),
            "COMFYUI_FACE_CONFIDENCE_THRESHOLD": os.getenv("COMFYUI_FACE_CONFIDENCE_THRESHOLD", "0.8"),
            "COMFYUI_FLUX_DIFFUSION_MODEL_NAME": os.getenv("COMFYUI_FLUX_DIFFUSION_MODEL_NAME", "flux1-schnell.safetensors"),
            "COMFYUI_FLUX_AE_NAME": os.getenv("COMFYUI_FLUX_AE_NAME", "ae.safetensors"),
            "COMFYUI_FLUX_CLIP_L_NAME": os.getenv("COMFYUI_FLUX_CLIP_L_NAME", "clip_l.safetensors"),
            "COMFYUI_FLUX_T5XXL_NAME": os.getenv("COMFYUI_FLUX_T5XXL_NAME", "t5xxl_fp8_e4m3fn.safetensors"),
        }
    )
)


@app.function(
    image=image,
    gpu="A10G",
    timeout=3600,
    scaledown_window=300,
    volumes={"/cache/models": model_cache_volume},
    secrets=[directus_secret],
)
@modal.asgi_app()
def fastapi_app():
    spec = importlib.util.spec_from_file_location("vixenbliss_s1_image_runtime", "/app/runtime/app.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.app
