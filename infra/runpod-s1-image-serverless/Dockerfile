FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TINI_SUBREAPER=1 \
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

ARG COMFYUI_REPO=https://github.com/Comfy-Org/ComfyUI.git
ARG COMFYUI_REF=ebf6b52e322664af91fcdc8b8848d31d5fb98f66
ARG COMFYUI_IPADAPTER_REPO=https://github.com/Shakker-Labs/ComfyUI-IPAdapter-Flux.git
ARG COMFYUI_IPADAPTER_REF=eef22b6875ddaf10f13657248b8123d6bdec2014
ARG COMFYUI_IMPACT_REPO=https://github.com/ltdrdata/ComfyUI-Impact-Pack.git
ARG COMFYUI_IMPACT_REF=6a517ebe06fea2b74fc41b3bd089c0d7173eeced
ARG TORCH_VERSION=2.6.0
ARG TORCHVISION_VERSION=0.21.0
ARG TORCHAUDIO_VERSION=2.6.0
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu124

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
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --index-url "${TORCH_INDEX_URL}" \
      "torch==${TORCH_VERSION}" \
      "torchvision==${TORCHVISION_VERSION}" \
      "torchaudio==${TORCHAUDIO_VERSION}" && \
    python -m pip install -r /tmp/runpod-s1-image-serverless-requirements.txt

RUN git init "${COMFYUI_HOME}" && \
    git -C "${COMFYUI_HOME}" remote add origin "${COMFYUI_REPO}" && \
    git -C "${COMFYUI_HOME}" fetch --depth 1 origin "${COMFYUI_REF}" && \
    git -C "${COMFYUI_HOME}" checkout --detach FETCH_HEAD && \
    git init "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-IPAdapter-Flux" && \
    git -C "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-IPAdapter-Flux" remote add origin "${COMFYUI_IPADAPTER_REPO}" && \
    git -C "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-IPAdapter-Flux" fetch --depth 1 origin "${COMFYUI_IPADAPTER_REF}" && \
    git -C "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-IPAdapter-Flux" checkout --detach FETCH_HEAD && \
    git init "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack" && \
    git -C "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack" remote add origin "${COMFYUI_IMPACT_REPO}" && \
    git -C "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack" fetch --depth 1 origin "${COMFYUI_IMPACT_REF}" && \
    git -C "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack" checkout --detach FETCH_HEAD

RUN python -m pip install -r "${COMFYUI_HOME}/requirements.txt" && \
    if [ -f "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-IPAdapter-Flux/requirements.txt" ]; then python -m pip install -r "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-IPAdapter-Flux/requirements.txt"; fi && \
    if [ -f "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack/requirements.txt" ]; then python -m pip install -r "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack/requirements.txt"; fi

# Re-apply the pinned torch stack after ComfyUI/plugin requirements so later
# installs cannot silently upgrade or downgrade it under our pinned runtime.
RUN python -m pip install --index-url "${TORCH_INDEX_URL}" \
      --upgrade --force-reinstall \
      "torch==${TORCH_VERSION}" \
      "torchvision==${TORCHVISION_VERSION}" \
      "torchaudio==${TORCHAUDIO_VERSION}"

COPY scripts /opt/runpod-s1-image-serverless/scripts
COPY workflows /opt/runpod-s1-image-serverless/workflows
COPY config /opt/runpod-s1-image-serverless/config
COPY handler.py /opt/runpod-s1-image-serverless/handler.py

RUN chmod +x /opt/runpod-s1-image-serverless/scripts/*.sh

ENTRYPOINT ["/usr/bin/tini", "--", "python", "/opt/runpod-s1-image-serverless/handler.py"]
