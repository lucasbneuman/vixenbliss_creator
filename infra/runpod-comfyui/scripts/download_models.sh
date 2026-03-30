#!/usr/bin/env bash
set -euo pipefail

COMFYUI_MODELS_DIR="${COMFYUI_MODELS_DIR:-/opt/comfyui/models}"
COMFYUI_IP_ADAPTER_MODEL="${COMFYUI_IP_ADAPTER_MODEL:-plus_face}"

mkdir -p "${COMFYUI_MODELS_DIR}/checkpoints" \
         "${COMFYUI_MODELS_DIR}/ipadapter" \
         "${COMFYUI_MODELS_DIR}/vae"

download_if_present() {
  local url="$1"
  local target="$2"
  if [ -n "${url}" ] && [ "${url}" != "CHANGEME" ]; then
    curl -L --fail --retry 3 -o "${target}" "${url}"
  fi
}

download_if_present "${IPADAPTER_PLUS_FACE_URL:-}" "${COMFYUI_MODELS_DIR}/ipadapter/${COMFYUI_IP_ADAPTER_MODEL}.safetensors"
download_if_present "${CHECKPOINT_MODEL_URL:-}" "${COMFYUI_MODELS_DIR}/checkpoints/base-image-model.safetensors"
download_if_present "${VAE_MODEL_URL:-}" "${COMFYUI_MODELS_DIR}/vae/base-image.vae.safetensors"
