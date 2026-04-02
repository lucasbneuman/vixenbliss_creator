#!/usr/bin/env bash
set -euo pipefail

COMFYUI_HOME="${COMFYUI_HOME:-/opt/comfyui}"
COMFYUI_PORT="${COMFYUI_PORT:-8188}"
COMFYUI_LISTEN="${COMFYUI_LISTEN:-0.0.0.0}"
COMFYUI_BASE_URL="${COMFYUI_BASE_URL:-http://127.0.0.1:${COMFYUI_PORT}}"
COMFYUI_USER_DIR="${COMFYUI_USER_DIR:-${COMFYUI_HOME}/user/default}"
COMFYUI_WORKFLOW_IMAGE_ID="${COMFYUI_WORKFLOW_IDENTITY_ID:-${COMFYUI_WORKFLOW_IMAGE_ID:-base-image-ipadapter-impact}}"

/opt/runpod-s1-image-serverless/scripts/bootstrap.sh
/opt/runpod-s1-image-serverless/scripts/download_models.sh

mkdir -p "${COMFYUI_USER_DIR}/workflows"
cp -f "/opt/runpod-s1-image-serverless/workflows/${COMFYUI_WORKFLOW_IMAGE_ID}.json" "${COMFYUI_USER_DIR}/workflows/${COMFYUI_WORKFLOW_IMAGE_ID}.json"

if [ ! -f "${COMFYUI_HOME}/main.py" ]; then
  echo "ComfyUI bootstrap failed: main.py not found in ${COMFYUI_HOME}" >&2
  exit 1
fi

if python - <<'PY'
import json
import os
from urllib import request

base_url = os.environ.get("COMFYUI_BASE_URL", "http://127.0.0.1:8188").rstrip("/")
try:
    with request.urlopen(f"{base_url}/system_stats", timeout=2) as response:
        payload = json.loads(response.read().decode("utf-8"))
    raise SystemExit(0 if isinstance(payload, dict) else 1)
except Exception:
    raise SystemExit(1)
PY
then
  echo "ComfyUI already responding on ${COMFYUI_BASE_URL}"
  exit 0
fi

cd "${COMFYUI_HOME}"
exec python main.py --listen "${COMFYUI_LISTEN}" --port "${COMFYUI_PORT}"
