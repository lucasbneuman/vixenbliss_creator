#!/usr/bin/env bash
set -euo pipefail

COMFYUI_HOME="${COMFYUI_HOME:-/opt/comfyui}"
COMFYUI_CUSTOM_NODES_DIR="${COMFYUI_CUSTOM_NODES_DIR:-${COMFYUI_HOME}/custom_nodes}"
COMFYUI_USER_DIR="${COMFYUI_USER_DIR:-${COMFYUI_HOME}/user/default}"
COMFYUI_WORKFLOW_IMAGE_ID="${COMFYUI_WORKFLOW_IMAGE_ID:-base-image-ipadapter-impact}"

mkdir -p "${COMFYUI_CUSTOM_NODES_DIR}" "${COMFYUI_USER_DIR}/workflows"

if [ ! -f "${COMFYUI_HOME}/main.py" ]; then
  echo "ComfyUI runtime is incomplete: ${COMFYUI_HOME}/main.py was not baked into the image" >&2
  exit 1
fi

if [ ! -d "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI_IPAdapter_plus" ]; then
  echo "ComfyUI runtime is incomplete: IPAdapter Plus was not baked into the image" >&2
  exit 1
fi

if [ ! -d "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack" ]; then
  echo "ComfyUI runtime is incomplete: Impact Pack was not baked into the image" >&2
  exit 1
fi

if [ ! -f "/opt/runpod-comfyui/workflows/${COMFYUI_WORKFLOW_IMAGE_ID}.json" ]; then
  echo "ComfyUI runtime is incomplete: expected workflow ${COMFYUI_WORKFLOW_IMAGE_ID}.json was not found" >&2
  exit 1
fi
