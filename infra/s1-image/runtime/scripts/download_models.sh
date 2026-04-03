#!/usr/bin/env bash
set -euo pipefail

COMFYUI_MODELS_DIR="${COMFYUI_MODELS_DIR:-/opt/comfyui/models}"
COMFYUI_FLUX_DIFFUSION_MODEL_NAME="${COMFYUI_FLUX_DIFFUSION_MODEL_NAME:-flux1-schnell.safetensors}"
COMFYUI_FLUX_AE_NAME="${COMFYUI_FLUX_AE_NAME:-ae.safetensors}"
COMFYUI_FLUX_CLIP_L_NAME="${COMFYUI_FLUX_CLIP_L_NAME:-clip_l.safetensors}"
COMFYUI_FLUX_T5XXL_NAME="${COMFYUI_FLUX_T5XXL_NAME:-t5xxl_fp8_e4m3fn.safetensors}"
COMFYUI_IP_ADAPTER_MODEL="${COMFYUI_IP_ADAPTER_MODEL:-plus_face}"
MODEL_CACHE_ROOT="${MODEL_CACHE_ROOT:-${RUNPOD_MODELS_ROOT:-${RUNPOD_VOLUME_PATH:-/cache/models}}}"
MODEL_BOOTSTRAP_WAIT_SECONDS="${MODEL_BOOTSTRAP_WAIT_SECONDS:-45}"

resolve_ip_adapter_asset_name() {
  local requested="$1"
  if [ "${requested}" = "plus_face" ]; then
    echo "flux-ipadapter-face.safetensors"
    return
  fi
  echo "${requested}"
}

COMFYUI_IP_ADAPTER_ASSET_NAME="$(resolve_ip_adapter_asset_name "${COMFYUI_IP_ADAPTER_MODEL}")"
MODEL_CACHE_FLUX_DIFFUSION_PATH="${MODEL_CACHE_FLUX_DIFFUSION_PATH:-${MODEL_CACHE_ROOT}/diffusion_models/${COMFYUI_FLUX_DIFFUSION_MODEL_NAME}}"
MODEL_CACHE_FLUX_AE_PATH="${MODEL_CACHE_FLUX_AE_PATH:-${MODEL_CACHE_ROOT}/vae/${COMFYUI_FLUX_AE_NAME}}"
MODEL_CACHE_FLUX_CLIP_L_PATH="${MODEL_CACHE_FLUX_CLIP_L_PATH:-${MODEL_CACHE_ROOT}/text_encoders/${COMFYUI_FLUX_CLIP_L_NAME}}"
MODEL_CACHE_FLUX_T5XXL_PATH="${MODEL_CACHE_FLUX_T5XXL_PATH:-${MODEL_CACHE_ROOT}/text_encoders/${COMFYUI_FLUX_T5XXL_NAME}}"
MODEL_CACHE_IPADAPTER_FLUX_PATH="${MODEL_CACHE_IPADAPTER_FLUX_PATH:-${MODEL_CACHE_ROOT}/ipadapter-flux/flux-ipadapter-face.safetensors}"

mkdir -p "${COMFYUI_MODELS_DIR}/diffusion_models" \
         "${COMFYUI_MODELS_DIR}/text_encoders" \
         "${COMFYUI_MODELS_DIR}/vae" \
         "${COMFYUI_MODELS_DIR}/ipadapter-flux"

link_or_copy_from_cache() {
  local source="$1"
  local target="$2"
  if [ -f "${source}" ] && [ ! -f "${target}" ]; then
    ln -sf "${source}" "${target}" || cp -f "${source}" "${target}"
  fi
}

wait_for_cache_file() {
  local source="$1"
  local timeout="$2"

  if [ -f "${source}" ]; then
    return 0
  fi

  local waited=0
  while [ "${waited}" -lt "${timeout}" ]; do
    if [ -f "${source}" ]; then
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done

  return 1
}

download_if_present() {
  local url="$1"
  local target="$2"
  if [ -n "${url}" ] && [ "${url}" != "CHANGEME" ] && [ ! -f "${target}" ]; then
    curl -L --fail --retry 3 -o "${target}" "${url}"
  fi
}

for source in \
  "${MODEL_CACHE_FLUX_DIFFUSION_PATH}" \
  "${MODEL_CACHE_FLUX_AE_PATH}" \
  "${MODEL_CACHE_FLUX_CLIP_L_PATH}" \
  "${MODEL_CACHE_FLUX_T5XXL_PATH}" \
  "${MODEL_CACHE_IPADAPTER_FLUX_PATH}"
do
  wait_for_cache_file "${source}" "${MODEL_BOOTSTRAP_WAIT_SECONDS}" || true
done

link_or_copy_from_cache "${MODEL_CACHE_FLUX_DIFFUSION_PATH}" "${COMFYUI_MODELS_DIR}/diffusion_models/${COMFYUI_FLUX_DIFFUSION_MODEL_NAME}"
link_or_copy_from_cache "${MODEL_CACHE_FLUX_AE_PATH}" "${COMFYUI_MODELS_DIR}/vae/${COMFYUI_FLUX_AE_NAME}"
link_or_copy_from_cache "${MODEL_CACHE_FLUX_CLIP_L_PATH}" "${COMFYUI_MODELS_DIR}/text_encoders/${COMFYUI_FLUX_CLIP_L_NAME}"
link_or_copy_from_cache "${MODEL_CACHE_FLUX_T5XXL_PATH}" "${COMFYUI_MODELS_DIR}/text_encoders/${COMFYUI_FLUX_T5XXL_NAME}"
link_or_copy_from_cache "${MODEL_CACHE_IPADAPTER_FLUX_PATH}" "${COMFYUI_MODELS_DIR}/ipadapter-flux/${COMFYUI_IP_ADAPTER_ASSET_NAME}"

download_if_present "${FLUX_DIFFUSION_MODEL_URL:-}" "${COMFYUI_MODELS_DIR}/diffusion_models/${COMFYUI_FLUX_DIFFUSION_MODEL_NAME}"
download_if_present "${FLUX_AE_URL:-}" "${COMFYUI_MODELS_DIR}/vae/${COMFYUI_FLUX_AE_NAME}"
download_if_present "${FLUX_CLIP_L_URL:-}" "${COMFYUI_MODELS_DIR}/text_encoders/${COMFYUI_FLUX_CLIP_L_NAME}"
download_if_present "${FLUX_T5XXL_URL:-}" "${COMFYUI_MODELS_DIR}/text_encoders/${COMFYUI_FLUX_T5XXL_NAME}"
download_if_present "${IPADAPTER_FLUX_URL:-}" "${COMFYUI_MODELS_DIR}/ipadapter-flux/${COMFYUI_IP_ADAPTER_ASSET_NAME}"

for target in \
  "${COMFYUI_MODELS_DIR}/diffusion_models/${COMFYUI_FLUX_DIFFUSION_MODEL_NAME}" \
  "${COMFYUI_MODELS_DIR}/vae/${COMFYUI_FLUX_AE_NAME}" \
  "${COMFYUI_MODELS_DIR}/text_encoders/${COMFYUI_FLUX_CLIP_L_NAME}" \
  "${COMFYUI_MODELS_DIR}/text_encoders/${COMFYUI_FLUX_T5XXL_NAME}" \
  "${COMFYUI_MODELS_DIR}/ipadapter-flux/${COMFYUI_IP_ADAPTER_ASSET_NAME}"
do
  if [ ! -f "${target}" ]; then
    echo "Required runtime asset is missing after model bootstrap: ${target}" >&2
    exit 1
  fi
done
