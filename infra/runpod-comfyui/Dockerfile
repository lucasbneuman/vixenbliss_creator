FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    COMFYUI_HOME=/opt/comfyui \
    COMFYUI_PORT=8188 \
    COMFYUI_LISTEN=0.0.0.0 \
    COMFYUI_WORKFLOW_IMAGE_ID=base-image-ipadapter-impact \
    COMFYUI_WORKFLOW_IMAGE_VERSION=2026-03-30 \
    COMFYUI_IP_ADAPTER_MODEL=plus_face \
    COMFYUI_FACE_CONFIDENCE_THRESHOLD=0.8 \
    COMFYUI_CUSTOM_NODES_DIR=/opt/comfyui/custom_nodes \
    COMFYUI_MODELS_DIR=/opt/comfyui/models \
    COMFYUI_USER_DIR=/opt/comfyui/user/default

WORKDIR /opt

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    tini \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/runpod-comfyui-requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install -r /tmp/runpod-comfyui-requirements.txt

COPY scripts /opt/runpod-comfyui/scripts
COPY workflows /opt/runpod-comfyui/workflows
COPY config /opt/runpod-comfyui/config

RUN chmod +x /opt/runpod-comfyui/scripts/*.sh

ENTRYPOINT ["/usr/bin/tini", "--", "/opt/runpod-comfyui/scripts/entrypoint.sh"]
