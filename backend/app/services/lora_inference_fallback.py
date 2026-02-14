import os
import base64
from typing import Optional, Dict, Any

from PIL import Image
from io import BytesIO


async def fallback_generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Simple local fallback that returns a 1x1 PNG base64 when no provider available.

    Controlled via env `ENABLE_REPLICATE_FALLBACK=true`. This is a safe default for
    local testing to avoid calling external APIs during CI.
    """
    # Always generate fallback; caller is responsible for checking if fallback is enabled.
    # Create 1x1 transparent PNG
    img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return {
        "image_base64": b64,
        "image_url": None,
        "generation_time": 0.01,
        "parameters": {"prompt": prompt, "resolution": f"{width}x{height}"},
        "model_info": {"provider": "replicate-fallback"},
        "cost": 0.0,
    }
