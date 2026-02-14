"""
Serverless Image LoRA Client (Modal-compatible)
Communicates with any HTTP serverless image endpoint via JSON payloads.
"""

import os
import time
import asyncio
import httpx
import base64
import logging
from typing import Any, Dict, Optional
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)


class ModalSDXLLoRAClient:
    """
    Client for Modal Serverless SDXL endpoint with dynamic LoRA loading.
    
    Modal expects:
    - prompt, negative_prompt, steps, cfg, width, height, seed (standard)
    - lora_url: presigned URL to .safetensors file (optional)
    - lora_scale: influence of LoRA (0.0-1.0)
    
    Response:
    - image_base64: PNG as base64 string
    - generation_time_seconds: inference duration
    - model_info: metadata about model/LoRA applied
    """

    def __init__(self):
        # Provider-agnostic vars (preferred)
        self.endpoint_url = (
            os.getenv("AI_PROVIDER_ENDPOINT_URL")
            or os.getenv("MODAL_ENDPOINT_URL")
        )
        self.api_token = (
            os.getenv("AI_PROVIDER_API_TOKEN")
            or os.getenv("MODAL_API_TOKEN")
            or os.getenv("MODAL_API_KEY")
        )
        self.auth_header = os.getenv("AI_PROVIDER_AUTH_HEADER", "Authorization")
        self.auth_scheme = os.getenv("AI_PROVIDER_AUTH_SCHEME", "Bearer")
        self.timeout_seconds = float(os.getenv("MODAL_TIMEOUT_SECONDS", "300"))
        # resilience config
        self.max_retries = int(os.getenv("MODAL_MAX_RETRIES", "3"))
        self.retry_backoff_base = float(os.getenv("MODAL_RETRY_BACKOFF_BASE", "1.0"))

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_token:
            headers[self.auth_header] = f"{self.auth_scheme} {self.api_token}".strip()
        return headers

    async def generate_image_with_lora(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        lora_url: Optional[str] = None,
        lora_scale: float = 0.9,
        steps: int = 28,
        cfg: float = 5.5,
    ) -> Dict[str, Any]:
        """
        Generate image with optional LoRA weights via Modal Serverless.

        Args:
            prompt: Generation prompt
            negative_prompt: Things to avoid
            width: Image width (default 1024)
            height: Image height (default 1024)
            seed: Random seed for reproducibility
            lora_url: Presigned URL to .safetensors LoRA weights
            lora_scale: LoRA influence (0.0-1.0, default 0.9)
            steps: Inference steps (default 28)
            cfg: Guidance scale (default 5.5)

        Returns:
            Dict with image_url, image_base64, generation_time, parameters
        """
        if not self.endpoint_url:
            raise ValueError("AI_PROVIDER_ENDPOINT_URL (or MODAL_ENDPOINT_URL) not configured")

        start_time = time.time()

        # Build request payload
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "width": width,
            "height": height,
            "steps": steps,
            "cfg": cfg,
        }

        if seed is not None:
            payload["seed"] = seed

        if lora_url:
            payload["lora_url"] = lora_url
            payload["lora_scale"] = lora_scale

        headers = self._get_headers()

        logger.info(
            f"[Modal SDXL LoRA] Submitting request: "
            f"prompt={prompt[:50]}..., "
            f"lora_applied={bool(lora_url)}, "
            f"resolution={width}x{height}"
        )

        # Masked debug for lora_url
        def _mask_url(u: Optional[str]) -> str:
            if not u:
                return "<none>"
            try:
                # keep scheme+host and mask query
                parts = u.split("//", 1)
                if len(parts) == 2:
                    host_and_rest = parts[1]
                    host = host_and_rest.split("/", 1)[0]
                    return f"{parts[0]}//{host}/..."
            except Exception:
                pass
            return "<masked_url>"

        logger.debug(f"[Modal SDXL LoRA] lora_url={_mask_url(lora_url)}")

        # Helper: detect simple presigned URL TTL hints
        def _is_presigned_url_expiring_soon(u: Optional[str], threshold: int = 300) -> bool:
            if not u:
                return False
            try:
                # look for common query params
                q = u.split("?", 1)[1] if "?" in u else ""
                params = {k.lower(): v for (k, v) in (p.split("=", 1) for p in q.split("&") if p)}
                for key in ("expires", "x-amz-expires", "exp", "expires_at", "expiry"):
                    if key in params:
                        val = params[key]
                        # numeric unix timestamp or seconds
                        try:
                            ival = int(val)
                            # if looks like unix timestamp ( > 1e9 )
                            now = int(time.time())
                            if ival > 1000000000:
                                return (ival - now) < threshold
                            else:
                                return ival < threshold
                        except Exception:
                            continue
            except Exception:
                return False
            return False

        if lora_url and _is_presigned_url_expiring_soon(lora_url):
            logger.warning("[Modal SDXL LoRA] lora_url appears to be expiring soon")

        attempt = 0
        last_exception = None
        while attempt < self.max_retries:
            attempt += 1
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        self.endpoint_url,
                        json=payload,
                        headers=headers,
                    )

                    if response.status_code >= 400:
                        error_data = response.json() if response.text else {}
                        error_msg = error_data.get("error", f"HTTP {response.status_code}")
                        error_code = error_data.get("error_code", "UNKNOWN")
                        logger.error(
                            f"[Modal SDXL LoRA] Request failed: {error_code} - {error_msg} (attempt {attempt}/{self.max_retries})"
                        )
                        raise Exception(f"Modal request failed: {error_code} - {error_msg}")

                    response.raise_for_status()
                    output = response.json()

                    generation_time = time.time() - start_time
                    return self._process_output(output, generation_time, payload)

            except httpx.TimeoutException as e:
                logger.warning(f"[Modal SDXL LoRA] Timeout on attempt {attempt}/{self.max_retries}")
                last_exception = e
            except httpx.HTTPError as e:
                logger.warning(f"[Modal SDXL LoRA] HTTPError on attempt {attempt}/{self.max_retries}: {str(e)}")
                last_exception = e
            except Exception as e:
                logger.warning(f"[Modal SDXL LoRA] Error on attempt {attempt}/{self.max_retries}: {str(e)}")
                last_exception = e

            # Backoff before next attempt
            if attempt < self.max_retries:
                backoff = self.retry_backoff_base * (2 ** (attempt - 1))
                logger.debug(f"[Modal SDXL LoRA] Backing off {backoff}s before retry")
                await asyncio.sleep(backoff)

        # All attempts failed
        logger.error(f"[Modal SDXL LoRA] All {self.max_retries} attempts failed")
        if last_exception:
            raise last_exception
        raise Exception("Modal request failed after retries")

    def _process_output(
        self,
        output: Dict[str, Any],
        total_time: float,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract image from Modal output and return result dict"""

        image_base64 = output.get("image_base64")
        if not image_base64:
            raise ValueError("Modal output missing image_base64")

        # Optionally decode to verify integrity
        try:
            img_data = base64.b64decode(image_base64)
            img = Image.open(BytesIO(img_data))
            logger.info(f"[Modal SDXL LoRA] Image decoded: {img.size}")
        except Exception as e:
            logger.warning(f"[Modal SDXL LoRA] Could not verify image: {str(e)}")

        model_info = output.get("model_info", {})
        generation_time = output.get("generation_time_seconds", total_time)

        return {
            "image_base64": image_base64,
            "image_url": None,  # Can be set later if saved to R2
            "generation_time": generation_time,
            "parameters": {
                "prompt": payload.get("prompt"),
                "negative_prompt": payload.get("negative_prompt"),
                "steps": payload.get("steps"),
                "cfg": payload.get("cfg"),
                "resolution": f"{payload.get('width')}x{payload.get('height')}",
                "seed": payload.get("seed"),
                "lora_scale": payload.get("lora_scale", 0.9),
            },
            "model_info": model_info,
            "cost": 0.001,  # Estimate: Modal serverless cost (varies by runtime)
        }

    async def save_image_to_r2(
        self,
        image_base64: str,
        avatar_id: str,
        tier: str = "capa1",
        storage_service: Optional[Any] = None,
    ) -> str:
        """
        Optional: Save base64 image to R2 and return presigned URL.
        Requires storage_service instance.
        """
        if not storage_service:
            logger.warning("[Modal SDXL LoRA] storage_service not provided, skipping R2 save")
            return None

        try:
            import uuid as uuid_pkg

            image_data = base64.b64decode(image_base64)
            file_path = f"content/{avatar_id}/{uuid_pkg.uuid4()}.png"

            result = storage_service.upload_file(
                file_content=image_data,
                file_path=file_path,
                content_type="image/png",
                metadata={"avatar_id": str(avatar_id), "tier": tier},
            )

            r2_url = result.get("r2_url")
            logger.info(f"[Modal SDXL LoRA] Saved to R2: {r2_url}")
            return r2_url

        except Exception as e:
            logger.error(f"[Modal SDXL LoRA] Failed to save to R2: {str(e)}")
            raise


# Singleton instance
modal_sdxl_lora_client = ModalSDXLLoRAClient()
