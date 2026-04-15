FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    PYTHONPATH=/app/src \
    VB_WEB_PUBLIC_ROOT=/app/apps/web/public \
    S1_IMAGE_EXECUTION_BACKEND=modal \
    COMFYUI_WORKFLOW_IDENTITY_ID=lora-dataset-ipadapter-batch \
    COMFYUI_WORKFLOW_IMAGE_ID=lora-dataset-ipadapter-batch \
    COMFYUI_WORKFLOW_IDENTITY_VERSION=2026-04-08 \
    COMFYUI_WORKFLOW_IMAGE_VERSION=2026-04-08

WORKDIR /app

COPY requirements.txt /tmp/root-requirements.txt
COPY infra/s1-image/runtime/requirements.txt /tmp/runtime-requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install -r /tmp/root-requirements.txt && \
    python -m pip install -r /tmp/runtime-requirements.txt

COPY apps /app/apps
COPY infra/s1-image/runtime /app/runtime
COPY src /app/src

EXPOSE 8000

CMD ["sh", "-c", "uvicorn runtime.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
