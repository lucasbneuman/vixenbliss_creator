FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    COMFYUI_HOME=/opt/comfyui \
    COMFYUI_PORT=8188 \
    COMFYUI_LISTEN=0.0.0.0 \
    COMFYUI_BASE_URL=http://127.0.0.1:8188 \
    COMFYUI_WORKFLOW_IDENTITY_ID=base-image-ipadapter-impact \
    COMFYUI_WORKFLOW_IDENTITY_VERSION=2026-03-31 \
    COMFYUI_WORKFLOW_IMAGE_ID=base-image-ipadapter-impact \
    COMFYUI_WORKFLOW_IMAGE_VERSION=2026-03-31 \
    COMFYUI_FLUX_DIFFUSION_MODEL_NAME=flux1-schnell.safetensors \
    COMFYUI_FLUX_AE_NAME=ae.safetensors \
    COMFYUI_FLUX_CLIP_L_NAME=clip_l.safetensors \
    COMFYUI_FLUX_T5XXL_NAME=t5xxl_fp8_e4m3fn.safetensors \
    COMFYUI_IP_ADAPTER_MODEL=flux-ipadapter-face.safetensors \
    COMFYUI_IP_ADAPTER_CLIP_VISION_MODEL=google/siglip-so400m-patch14-384 \
    COMFYUI_FACE_CONFIDENCE_THRESHOLD=0.8 \
    COMFYUI_CUSTOM_NODES_DIR=/opt/comfyui/custom_nodes \
    COMFYUI_MODELS_DIR=/opt/comfyui/models \
    COMFYUI_USER_DIR=/opt/comfyui/user/default \
    COMFYUI_INPUT_DIR=/opt/comfyui/input

ARG COMFYUI_REPO=https://github.com/comfyanonymous/ComfyUI.git
ARG COMFYUI_REF=master
ARG COMFYUI_IPADAPTER_REPO=https://github.com/Shakker-Labs/ComfyUI-IPAdapter-Flux.git
ARG COMFYUI_IPADAPTER_REF=main
ARG COMFYUI_IMPACT_REPO=https://github.com/ltdrdata/ComfyUI-Impact-Pack.git
ARG COMFYUI_IMPACT_REF=Main

WORKDIR /opt

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    tini \
    python3 \
    python3-pip \
    python3-venv \
    python-is-python3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/runpod-s1-image-serverless-requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install --index-url https://download.pytorch.org/whl/cu118 \
      torch==2.3.1 \
      torchvision==0.18.1 \
      torchaudio==2.3.1 && \
    python -m pip install -r /tmp/runpod-s1-image-serverless-requirements.txt

RUN git clone --depth 1 --branch "${COMFYUI_REF}" "${COMFYUI_REPO}" "${COMFYUI_HOME}" && \
    git clone --depth 1 --branch "${COMFYUI_IPADAPTER_REF}" "${COMFYUI_IPADAPTER_REPO}" "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-IPAdapter-Flux" && \
    git clone --depth 1 --branch "${COMFYUI_IMPACT_REF}" "${COMFYUI_IMPACT_REPO}" "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack"

RUN python -m pip install -r "${COMFYUI_HOME}/requirements.txt" && \
    if [ -f "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-IPAdapter-Flux/requirements.txt" ]; then python -m pip install -r "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-IPAdapter-Flux/requirements.txt"; fi && \
    if [ -f "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack/requirements.txt" ]; then python -m pip install -r "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack/requirements.txt"; fi

# Re-apply the pinned CUDA 11.8 torch stack after ComfyUI/plugin requirements so
# later installs cannot silently upgrade torch to a less compatible build.
RUN python -m pip install --index-url https://download.pytorch.org/whl/cu118 \
      --upgrade --force-reinstall \
      torch==2.3.1 \
      torchvision==0.18.1 \
      torchaudio==2.3.1

COPY scripts /opt/runpod-s1-image-serverless/scripts
COPY workflows /opt/runpod-s1-image-serverless/workflows
COPY config /opt/runpod-s1-image-serverless/config
COPY handler.py /opt/runpod-s1-image-serverless/handler.py

RUN chmod +x /opt/runpod-s1-image-serverless/scripts/*.sh

ENTRYPOINT ["/usr/bin/tini", "--", "python", "/opt/runpod-s1-image-serverless/handler.py"]
