import asyncio
import base64
from types import SimpleNamespace

import pytest

from app.api.content import generate_single_content
from app.schemas.content import ContentGenerationRequest


class FakeDB:
    def __init__(self, avatar):
        self._avatar = avatar
        self._last_added = None

    def query(self, model):
        class Q:
            def __init__(self, avatar):
                self.avatar = avatar

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return self.avatar

        return Q(self._avatar)

    # Minimal session methods used by endpoint
    def add(self, obj):
        self._last_added = obj

    def commit(self):
        return None

    def refresh(self, obj):
        return None


def test_generate_single_content_uses_fallback(monkeypatch):
    # Arrange
    avatar = SimpleNamespace(id="12345678-1234-5678-1234-567812345678", lora_weights_url="https://example.com/lora.safetensors", niche="fitness", aesthetic_style="sporty")
    db = FakeDB(avatar)

    req = ContentGenerationRequest(avatar_id=str(avatar.id), custom_prompt="woman in gym, smiling")

    # Simulate lora_inference failure
    async def fake_generate(*args, **kwargs):
        raise Exception("modal down")

    monkeypatch.setattr("app.services.lora_inference.lora_inference_engine.generate_image_with_lora", fake_generate)

    # Patch fallback to return image base64
    async def fake_fallback(prompt, width=1024, height=1024, seed=None):
        b64 = base64.b64encode(b"x").decode()
        return {"image_base64": b64, "image_url": None, "generation_time": 0.01, "parameters": {"prompt": prompt}, "model_info": {"provider": "replicate-fallback"}, "cost": 0.0}

    monkeypatch.setenv("ENABLE_REPLICATE_FALLBACK", "true")
    monkeypatch.setattr("app.services.lora_inference_fallback.fallback_generate_image", fake_fallback)

    # Act
    res = asyncio.run(generate_single_content(request=req, db=db))

    # Assert: endpoint returns ContentPiece-like object with url data:image/png;base64,...
    assert hasattr(res, "url")
    assert res.url.startswith("data:image/png;base64,")
