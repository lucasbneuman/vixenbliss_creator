from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "infra" / "comfyui-copilot"
RUNTIME = BUNDLE / "runtime"


def test_comfyui_copilot_bundle_contains_expected_files() -> None:
    expected = [
        BUNDLE / "README.md",
        RUNTIME / "app.py",
        RUNTIME / "requirements.txt",
        BUNDLE / "providers" / "modal" / "app.py",
    ]

    for path in expected:
        assert path.exists(), f"missing deployable artifact: {path}"


def test_comfyui_copilot_modal_wrapper_uses_openai_secret() -> None:
    modal_app = (BUNDLE / "providers" / "modal" / "app.py").read_text(encoding="utf-8")

    assert 'modal.Secret.from_name("vixenbliss-s1-llm-openai")' in modal_app
    assert '@modal.asgi_app()' in modal_app
    assert 'COMFYUI_COPILOT_DEFAULT_STAGE' in modal_app
