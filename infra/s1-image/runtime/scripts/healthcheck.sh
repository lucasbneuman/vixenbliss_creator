#!/usr/bin/env bash
set -euo pipefail

COMFYUI_BASE_URL="${COMFYUI_BASE_URL:-http://127.0.0.1:8188}"

python - <<'PY'
import json
import os
from urllib import request

base_url = os.environ.get("COMFYUI_BASE_URL", "http://127.0.0.1:8188").rstrip("/")
with request.urlopen(f"{base_url}/system_stats", timeout=5) as response:
    payload = json.loads(response.read().decode("utf-8"))
if not isinstance(payload, dict):
    raise SystemExit(1)
PY
