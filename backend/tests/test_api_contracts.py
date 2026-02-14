"""API contract freeze tests for critical endpoints in the current app wiring."""

from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(override_get_db):
    return TestClient(app)


def _assert_has_detail(payload):
    assert isinstance(payload, dict)
    assert "detail" in payload


def test_health_contract(client):
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "database" in data


def test_identities_list_requires_user_id_query_contract(client):
    response = client.get("/api/v1/identities/avatars")
    assert response.status_code == 422
    _assert_has_detail(response.json())


def test_identities_get_avatar_not_found_contract(client):
    response = client.get(f"/api/v1/identities/avatars/{uuid4()}")
    assert response.status_code == 404
    _assert_has_detail(response.json())


def test_content_generate_body_validation_contract(client):
    response = client.post("/api/v1/content/generate", json={})
    assert response.status_code == 422
    _assert_has_detail(response.json())


def test_error_shape_contract_for_unknown_path(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    _assert_has_detail(response.json())


def test_loras_models_forbidden_on_user_mismatch_with_jwt(client, monkeypatch):
    from jose import jwt
    import app.api.dependencies as deps

    token_user_id = str(uuid4())
    requested_user_id = str(uuid4())

    monkeypatch.setattr(deps, "USE_JWT_AUTH", True)
    monkeypatch.setattr(deps, "SECRET_KEY", "testsecret")

    token = jwt.encode({"sub": token_user_id}, "testsecret", algorithm="HS256")

    response = client.get(
        f"/api/v1/loras/models?user_id={requested_user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    _assert_has_detail(response.json())


def test_avatar_response_keeps_metadata_contract_key():
    from app.schemas.identity import AvatarResponse

    payload = SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        name="Contract Avatar",
        stage="lora_ready",
        base_image_url="https://example.com/base.png",
        lora_model_id=None,
        niche="fitness",
        aesthetic_style="natural",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        meta_data={"contract": "ok"},
    )

    data = AvatarResponse.model_validate(payload).model_dump()
    assert "metadata" in data
    assert "meta_data" not in data


def test_content_safety_returns_503_when_service_unavailable(client, monkeypatch):
    import app.api.content as content_api

    monkeypatch.setattr(content_api, "content_safety_service", None)

    response = client.post(
        "/api/v1/content/safety-check",
        json={"image_url": "https://example.com/image.jpg", "prompt": "safe"},
    )
    assert response.status_code == 503
    _assert_has_detail(response.json())
