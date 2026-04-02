from __future__ import annotations

import modal


app = modal.App("vixenbliss-s1-image")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements("infra/s1-image/runtime/requirements.txt")
    .add_local_dir("src", remote_path="/root/src")
    .add_local_file("infra/s1-image/runtime/app.py", "/root/app.py")
    .env({"PYTHONPATH": "/root/src"})
)


@app.function(image=image, gpu="A10G", timeout=1800)
@modal.asgi_app()
def fastapi_app():
    from app import app as web_app

    return web_app
