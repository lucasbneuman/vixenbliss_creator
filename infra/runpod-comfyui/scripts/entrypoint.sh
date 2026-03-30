#!/usr/bin/env bash
set -euo pipefail

COMFYUI_HOME="${COMFYUI_HOME:-/opt/comfyui}"
COMFYUI_PORT="${COMFYUI_PORT:-8188}"
COMFYUI_LISTEN="${COMFYUI_LISTEN:-0.0.0.0}"
COMFYUI_USER_DIR="${COMFYUI_USER_DIR:-${COMFYUI_HOME}/user/default}"
COMFYUI_WORKFLOW_IMAGE_ID="${COMFYUI_WORKFLOW_IMAGE_ID:-base-image-ipadapter-impact}"

/opt/runpod-comfyui/scripts/bootstrap.sh
/opt/runpod-comfyui/scripts/download_models.sh || true

mkdir -p "${COMFYUI_USER_DIR}/workflows"
cp "/opt/runpod-comfyui/workflows/${COMFYUI_WORKFLOW_IMAGE_ID}.json" "${COMFYUI_USER_DIR}/workflows/${COMFYUI_WORKFLOW_IMAGE_ID}.json"

if [ ! -f "${COMFYUI_HOME}/main.py" ]; then
  echo "ComfyUI bootstrap failed: main.py not found in ${COMFYUI_HOME}" >&2
  exit 1
fi

cd "${COMFYUI_HOME}"
exec python main.py --listen "${COMFYUI_LISTEN}" --port "${COMFYUI_PORT}"
