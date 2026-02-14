import asyncio
import base64
import os
from types import SimpleNamespace

import pytest
import httpx

from app.services.modal_sdxl_lora_client import ModalSDXLLoRAClient


class DummyTimeout(Exception):
    pass


class FakeAsyncClient:
    def __init__(self, responses):
        self._responses = responses

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        # Pop first response
        if not self._responses:
            raise Exception("No more fake responses")
        resp = self._responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp


class DummyResponse:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self._body = body or {}
        self.text = "json"

    def json(self):
        return self._body
    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("status", request=None, response=None)


def test_modal_retries_success(monkeypatch):
    client = ModalSDXLLoRAClient()
    # prepare: first two attempts timeout, third returns success
    fake_responses = [
        httpx.TimeoutException("timeout"),
        httpx.TimeoutException("timeout2"),
        DummyResponse(status_code=200, body={"image_base64": base64.b64encode(b"x").decode()}),
    ]

    # Monkeypatch AsyncClient
    def fake_async_client_factory(*args, **kwargs):
        # Provide the same list instance across attempts so pops advance across retries
        return FakeAsyncClient(fake_responses)

    monkeypatch.setattr("app.services.modal_sdxl_lora_client.httpx.AsyncClient", fake_async_client_factory)

    # Also monkeypatch process_output to avoid PIL decode in test
    async def run():
        res = await client.generate_image_with_lora(prompt="test")
        assert res.get("image_base64") is not None

    asyncio.run(run())
