"""
ComfyUI Client
Sends prompt workflows to a ComfyUI server (e.g. serverless GPU) and fetches output URLs.
"""

import os
import json
import time
import asyncio
import httpx
from typing import Any, Dict, Optional


def _replace_tokens(obj: Any, mapping: Dict[str, str]) -> Any:
    if isinstance(obj, dict):
        return {k: _replace_tokens(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_replace_tokens(v, mapping) for v in obj]
    if isinstance(obj, str):
        out = obj
        for key, val in mapping.items():
            out = out.replace(key, val)
        return out
    return obj


class ComfyUIClient:
    def __init__(self) -> None:
        self.api_url = os.getenv("COMFYUI_API_URL")
        self.workflow_path = os.getenv("COMFYUI_WORKFLOW_JSON")
        self.poll_seconds = float(os.getenv("COMFYUI_POLL_SECONDS", "2"))
        self.timeout_seconds = float(os.getenv("COMFYUI_TIMEOUT_SECONDS", "180"))

    def _load_workflow(self) -> Dict[str, Any]:
        if not self.workflow_path:
            raise ValueError("COMFYUI_WORKFLOW_JSON is not configured")
        with open(self.workflow_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_workflow(self, mapping: Dict[str, str]) -> Dict[str, Any]:
        workflow = self._load_workflow()
        return _replace_tokens(workflow, mapping)

    def _build_image_url(self, filename: str, subfolder: str = "", file_type: str = "output") -> str:
        # Standard ComfyUI view endpoint
        return f"{self.api_url}/view?filename={filename}&subfolder={subfolder}&type={file_type}"

    async def generate_image_with_lora(
        self,
        prompt: str,
        negative_prompt: Optional[str],
        width: int,
        height: int,
        seed: Optional[int],
        lora_url: str,
        lora_scale: float = 0.8
    ) -> Dict[str, Any]:
        if not self.api_url:
            raise ValueError("COMFYUI_API_URL is not configured")

        mapping = {
            "{{PROMPT}}": prompt,
            "{{NEGATIVE_PROMPT}}": negative_prompt or "",
            "{{WIDTH}}": str(width),
            "{{HEIGHT}}": str(height),
            "{{SEED}}": str(seed or 0),
            "{{LORA_URL}}": lora_url,
            "{{LORA_SCALE}}": str(lora_scale)
        }

        workflow = self._build_workflow(mapping)

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.api_url}/prompt", json={"prompt": workflow}, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            prompt_id = data.get("prompt_id")
            if not prompt_id:
                raise ValueError("ComfyUI did not return prompt_id")

            # Poll history for completion
            start = time.time()
            while time.time() - start < self.timeout_seconds:
                hist = await client.get(f"{self.api_url}/history/{prompt_id}", timeout=30.0)
                if hist.status_code == 200:
                    history = hist.json()
                    if prompt_id in history:
                        outputs = history[prompt_id].get("outputs", {})
                        for node_id, node in outputs.items():
                            images = node.get("images", [])
                            if images:
                                img = images[0]
                                image_url = self._build_image_url(
                                    filename=img.get("filename", ""),
                                    subfolder=img.get("subfolder", ""),
                                    file_type=img.get("type", "output")
                                )
                                return {
                                    "image_url": image_url,
                                    "generation_time": time.time() - start,
                                    "parameters": {
                                        "prompt": prompt,
                                        "negative_prompt": negative_prompt,
                                        "width": width,
                                        "height": height,
                                        "seed": seed,
                                        "lora_weights": lora_url,
                                        "lora_scale": lora_scale
                                    },
                                    "cost": 0.0
                                }
                await asyncio.sleep(self.poll_seconds)

        raise TimeoutError("ComfyUI generation timed out")


comfyui_client = ComfyUIClient()

