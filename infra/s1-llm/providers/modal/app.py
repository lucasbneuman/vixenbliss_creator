from __future__ import annotations

import importlib.util
import os

import modal


APP_NAME = os.getenv("S1_LLM_MODAL_APP_NAME", "vixenbliss-s1-llm-gpt41mini")
LLM_BACKEND = os.getenv("S1_LLM_BACKEND", "openai").strip().lower()

app = modal.App(APP_NAME)

directus_secret = modal.Secret.from_name("vixenbliss-s1-control-plane")
openai_secret = modal.Secret.from_name("vixenbliss-s1-llm-openai")
ollama_volume = modal.Volume.from_name("vixenbliss-s1-llm-ollama-cache", create_if_missing=True)

base_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements("infra/s1-llm/runtime/requirements.txt")
    .add_local_dir("src", remote_path="/root/src", copy=True)
    .add_local_file("infra/s1-llm/runtime/app.py", remote_path="/root/runtime_app.py", copy=True)
)

if LLM_BACKEND == "ollama":
    image = (
        base_image.apt_install("curl", "ca-certificates", "zstd")
        .run_commands("curl -fsSL https://ollama.com/install.sh | sh")
        .env(
            {
                "PYTHONPATH": "/root/src",
                "S1_LLM_BACKEND": "ollama",
                "OLLAMA_STARTUP_ENABLED": "1",
                "OLLAMA_PULL_ON_START": "0",
                "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
                "S1_LLM_OPENAI_MODEL_ALIAS": os.getenv("S1_LLM_OPENAI_MODEL_ALIAS", os.getenv("OLLAMA_MODEL", "qwen2.5:3b")),
                "SERVICE_ARTIFACT_ROOT": "/root/data/artifacts",
            }
        )
    )
    runtime_kwargs = {
        "gpu": "L4",
        "volumes": {"/root/.ollama": ollama_volume},
    }
else:
    image = base_image.env(
        {
            "PYTHONPATH": "/root/src",
            "S1_LLM_BACKEND": "openai",
            "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            "S1_LLM_OPENAI_MODEL_ALIAS": os.getenv("S1_LLM_OPENAI_MODEL_ALIAS", os.getenv("OPENAI_MODEL", "gpt-4.1-mini")),
            "SERVICE_ARTIFACT_ROOT": "/root/data/artifacts",
        }
    )
    runtime_kwargs = {}


@app.function(
    image=image,
    timeout=3600,
    scaledown_window=300,
    secrets=[directus_secret, openai_secret],
    **runtime_kwargs,
)
@modal.asgi_app()
def fastapi_app():
    spec = importlib.util.spec_from_file_location("vixenbliss_s1_llm_runtime", "/root/runtime_app.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.web_app


@app.function(
    image=image,
    timeout=3600,
    scaledown_window=300,
    secrets=[directus_secret, openai_secret],
    **runtime_kwargs,
)
def prime_model_cache(model_name: str | None = None) -> dict[str, str]:
    if LLM_BACKEND != "ollama":
        return {"status": "skipped", "backend": LLM_BACKEND}

    import subprocess
    import time
    from urllib import request

    env = dict(os.environ)
    env["OLLAMA_HOST"] = "127.0.0.1:11434"
    target_model = model_name or os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    process = subprocess.Popen(
        ["ollama", "serve"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        deadline = time.time() + 90
        while time.time() < deadline:
            try:
                with request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5):
                    break
            except Exception:
                time.sleep(1)
        subprocess.run(["ollama", "pull", target_model], check=True, env=env)
        return {"status": "ready", "backend": LLM_BACKEND, "model": target_model}
    finally:
        process.terminate()
