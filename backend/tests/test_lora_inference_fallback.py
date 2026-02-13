import asyncio
import os
import base64

import pytest

from types import SimpleNamespace

from app.services.lora_inference import lora_inference_engine


class DummyAvatar:
    def __init__(self, id, lora_weights_url):
        self.id = id
        self.lora_weights_url = lora_weights_url


def test_modal_failure_uses_fallback(monkeypatch):
    # Arrange: ensure fallback enabled
    monkeypatch.setenv("ENABLE_REPLICATE_FALLBACK", "true")

    # Create dummy avatar
    avatar = DummyAvatar(id="12345678-1234-5678-1234-567812345678", lora_weights_url="https://example.com/lora.safetensors")

    # Monkeypatch modal client to raise
    async def fake_modal(*args, **kwargs):
        print("fake_modal called, raising exception")
        raise Exception("modal down")

    monkeypatch.setattr("app.services.lora_inference.modal_sdxl_lora_client.generate_image_with_lora", fake_modal)

    # Monkeypatch fallback to return a small PNG base64
    async def fake_fallback(prompt, width=1024, height=1024, seed=None):
        print(f"fake_fallback called with prompt={prompt}")
        b64 = base64.b64encode(b"x").decode()
        result = {"image_base64": b64, "image_url": None, "generation_time": 0.01, "parameters": {"prompt": prompt}, "model_info": {"provider": "replicate-fallback"}, "cost": 0.0}
        print(f"fake_fallback returning: {result}")
        return result

    monkeypatch.setattr("app.services.lora_inference_fallback.fallback_generate_image", fake_fallback)

    # Mock _provider_chain to return the chain with fallback
    def fake_provider_chain(self):
        print("fake_provider_chain called, returning ['modal_sdxl_lora', 'replicate-fallback']")
        return ["modal_sdxl_lora", "replicate-fallback"]

    monkeypatch.setattr("app.services.lora_inference.LoRAInferenceEngine._provider_chain", fake_provider_chain)

    # Act
    try:
        res = asyncio.run(lora_inference_engine.generate_image_with_lora(avatar=avatar, prompt="test prompt"))
        print(f"Result: {res}")
    except Exception as e:
        print(f"Exception raised: {e}")
        raise

    # Assert
    assert res.get("image_base64") is not None or res.get("image_url") is not None
    assert res.get("model_info", {}).get("provider") == "replicate-fallback"
