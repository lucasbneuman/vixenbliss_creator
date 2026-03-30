#!/usr/bin/env bash
set -euo pipefail

COMFYUI_HOME="${COMFYUI_HOME:-/opt/comfyui}"
COMFYUI_CUSTOM_NODES_DIR="${COMFYUI_CUSTOM_NODES_DIR:-${COMFYUI_HOME}/custom_nodes}"
COMFYUI_USER_DIR="${COMFYUI_USER_DIR:-${COMFYUI_HOME}/user/default}"

mkdir -p "${COMFYUI_CUSTOM_NODES_DIR}" "${COMFYUI_USER_DIR}/workflows"

if [ ! -d "${COMFYUI_HOME}/.git" ]; then
  git clone https://github.com/comfyanonymous/ComfyUI.git "${COMFYUI_HOME}"
fi

python -m pip install --upgrade pip
python -m pip install -r "${COMFYUI_HOME}/requirements.txt"

if [ ! -d "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI_IPAdapter_plus" ]; then
  git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI_IPAdapter_plus"
fi

if [ ! -d "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack" ]; then
  git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack"
fi

if [ -f "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI_IPAdapter_plus/requirements.txt" ]; then
  python -m pip install -r "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI_IPAdapter_plus/requirements.txt"
fi

if [ -f "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack/requirements.txt" ]; then
  python -m pip install -r "${COMFYUI_CUSTOM_NODES_DIR}/ComfyUI-Impact-Pack/requirements.txt"
fi
