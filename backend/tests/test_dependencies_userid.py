import asyncio
import importlib
import uuid

import pytest
from fastapi import HTTPException


def test_query_param_ok():
    uid = str(uuid.uuid4())
    # Call dependency directly in default (JWT disabled) mode
    import app.api.dependencies as deps

    # Ensure fallback mode
    assert not deps.USE_JWT_AUTH

    res = asyncio.run(deps.get_user_id(authorization=None, q_user_id=uid))
    assert str(res) == uid


def test_missing_param_raises():
    import app.api.dependencies as deps

    with pytest.raises(HTTPException) as exc:
        asyncio.run(deps.get_user_id(authorization=None, q_user_id=None))
    assert exc.value.status_code == 422


def test_jwt_success(monkeypatch):
    # Enable JWT mode by setting env and reloading module
    monkeypatch.setenv("USE_JWT_AUTH", "true")
    monkeypatch.setenv("SECRET_KEY", "testsecret")

    import app.api.dependencies as deps
    importlib.reload(deps)

    uid = str(uuid.uuid4())
    from jose import jwt

    token = jwt.encode({"sub": uid}, "testsecret", algorithm="HS256")

    res = asyncio.run(deps.get_user_id(authorization=f"Bearer {token}", q_user_id=None))
    assert str(res) == uid


def test_jwt_invalid_token(monkeypatch):
    monkeypatch.setenv("USE_JWT_AUTH", "true")
    monkeypatch.setenv("SECRET_KEY", "testsecret")

    import app.api.dependencies as deps
    importlib.reload(deps)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(deps.get_user_id(authorization="Bearer invalid.token.here", q_user_id=None))
    assert exc.value.status_code == 401
