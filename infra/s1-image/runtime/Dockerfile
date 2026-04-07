FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    TINI_SUBREAPER=1 \
    PYTHONPATH=/app/src \
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
    COMFYUI_IP_ADAPTER_MODEL=plus_face \
    COMFYUI_IP_ADAPTER_CLIP_VISION_MODEL=google/siglip-so400m-patch14-384 \
    COMFYUI_FACE_CONFIDENCE_THRESHOLD=0.8 \
    COMFYUI_CUSTOM_NODES_DIR=/opt/comfyui/custom_nodes \
    COMFYUI_MODELS_DIR=/opt/comfyui/models \
    COMFYUI_USER_DIR=/opt/comfyui/user/default \
    COMFYUI_INPUT_DIR=/opt/comfyui/input \
    MODEL_CACHE_ROOT=/cache/models

ARG COMFYUI_REPO=https://github.com/Comfy-Org/ComfyUI.git
ARG COMFYUI_REF=bda1482a272e36315d39ef84663073f88d0a0367
ARG COMFYUI_IPADAPTER_REPO=https://github.com/Shakker-Labs/ComfyUI-IPAdapter-Flux.git
ARG COMFYUI_IPADAPTER_REF=eef22b6875ddaf10f13657248b8123d6bdec2014
ARG COMFYUI_IMPACT_REPO=https://github.com/ltdrdata/ComfyUI-Impact-Pack.git
ARG COMFYUI_IMPACT_REF=6a517ebe06fea2b74fc41b3bd089c0d7173eeced
ARG COMFYUI_IMPACT_SUBPACK_REPO=https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git
ARG COMFYUI_IMPACT_SUBPACK_REF=50c7b71a6a224734cc9b21963c6d1926816a97f1
ARG TORCH_VERSION=2.5.1
ARG TORCHVISION_VERSION=0.20.1
ARG TORCHAUDIO_VERSION=2.5.1
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu124

WORKDIR /opt

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    tini \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    python3 \
    python3-pip \
    python3-venv \
    python-is-python3 \
    && rm -rf /var/lib/apt/lists/*

COPY infra/s1-image/runtime/requirements.txt /tmp/s1-image-requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --index-url "${TORCH_INDEX_URL}" \
      "torch==${TORCH_VERSION}" \
      "torchvision==${TORCHVISION_VERSION}" \
      "torchaudio==${TORCHAUDIO_VERSION}" && \
    python -m pip install -r /tmp/s1-image-requirements.txt

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
    git -C "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack" checkout --detach FETCH_HEAD && \
    git init "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Subpack" && \
    git -C "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Subpack" remote add origin "${COMFYUI_IMPACT_SUBPACK_REPO}" && \
    git -C "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Subpack" fetch --depth 1 origin "${COMFYUI_IMPACT_SUBPACK_REF}" && \
    git -C "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Subpack" checkout --detach FETCH_HEAD

RUN python -c "from pathlib import Path; core_path = Path('/opt/comfyui/custom_nodes/ComfyUI-Impact-Pack/modules/impact/core.py'); original = 'return list(comfy.samplers.SCHEDULER_HANDLERS) + ADDITIONAL_SCHEDULERS'; patched = \"return list(getattr(comfy.samplers, 'SCHEDULER_HANDLERS', comfy.samplers.SCHEDULER_NAMES)) + ADDITIONAL_SCHEDULERS\"; text = core_path.read_text(encoding='utf-8'); assert original in text, f'Expected Impact Pack scheduler hook not found in {core_path}'; core_path.write_text(text.replace(original, patched), encoding='utf-8')"

RUN python -m pip install -r "${COMFYUI_HOME}/requirements.txt" && \
    if [ -f "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-IPAdapter-Flux/requirements.txt" ]; then python -m pip install -r "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-IPAdapter-Flux/requirements.txt"; fi && \
    if [ -f "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack/requirements.txt" ]; then python -m pip install -r "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack/requirements.txt"; fi && \
    if [ -f "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Subpack/requirements.txt" ]; then python -m pip install -r "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Subpack/requirements.txt"; fi

RUN python -m pip install --index-url "${TORCH_INDEX_URL}" \
      --upgrade --force-reinstall \
      "torch==${TORCH_VERSION}" \
      "torchvision==${TORCHVISION_VERSION}" \
      "torchaudio==${TORCHAUDIO_VERSION}"

WORKDIR /app

COPY infra/s1-image/runtime /app/runtime
COPY src /app/src

RUN sed -i 's/\r$//' /app/runtime/scripts/*.sh && \
    chmod +x /app/runtime/scripts/*.sh

EXPOSE 8000

CMD ["uvicorn", "runtime.app:app", "--host", "0.0.0.0", "--port", "8000"]
