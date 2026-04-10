from __future__ import annotations

import importlib.util
import os

import modal


APP_NAME = os.getenv("COMFYUI_COPILOT_MODAL_APP_NAME", "vixenbliss-comfyui-copilot")

app = modal.App(APP_NAME)

openai_secret = modal.Secret.from_name("vixenbliss-s1-llm-openai")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements("infra/comfyui-copilot/runtime/requirements.txt")
    .add_local_dir("src", remote_path="/root/src", copy=True)
    .add_local_file("infra/comfyui-copilot/runtime/app.py", remote_path="/root/runtime_app.py", copy=True)
    .env(
        {
            "PYTHONPATH": "/root/src",
            "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "COMFYUI_COPILOT_TIMEOUT_SECONDS": os.getenv("COMFYUI_COPILOT_TIMEOUT_SECONDS", "60"),
            "COMFYUI_COPILOT_DEFAULT_STAGE": os.getenv("COMFYUI_COPILOT_DEFAULT_STAGE", "s1_identity_image"),
        }
    )
)


@app.function(
    image=image,
    timeout=1800,
    scaledown_window=300,
    secrets=[openai_secret],
)
@modal.asgi_app()
def fastapi_app():
    spec = importlib.util.spec_from_file_location("vixenbliss_comfyui_copilot_runtime", "/root/runtime_app.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.web_app
