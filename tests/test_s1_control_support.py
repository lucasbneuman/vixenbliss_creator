from __future__ import annotations

import os
from pathlib import Path

from vixenbliss_creator.s1_control.support import is_png_bytes, load_local_env, png_dimensions, tiny_png_bytes


def test_tiny_png_fixture_is_a_real_png() -> None:
    payload = tiny_png_bytes()

    assert len(payload) > 60
    assert is_png_bytes(payload) is True
    assert png_dimensions(payload) == (64, 64)


def test_load_local_env_uses_repo_dotenv_without_overwriting_existing_values(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    (repo_root / ".env").write_text("DIRECTUS_BASE_URL=https://directus.example.com\nDIRECTUS_API_TOKEN=secret\n", encoding="utf-8")
    monkeypatch.setattr("vixenbliss_creator.s1_control.support.repo_root", lambda: repo_root)
    monkeypatch.setenv("DIRECTUS_API_TOKEN", "existing-secret")
    monkeypatch.delenv("DIRECTUS_BASE_URL", raising=False)

    load_local_env()

    assert os.environ["DIRECTUS_BASE_URL"] == "https://directus.example.com"
    assert os.environ["DIRECTUS_API_TOKEN"] == "existing-secret"
