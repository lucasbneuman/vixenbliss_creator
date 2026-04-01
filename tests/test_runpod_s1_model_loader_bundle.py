from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "infra" / "runpod-s1-model-loader"


def test_runpod_s1_model_loader_bundle_contains_expected_files() -> None:
    expected = [
        BUNDLE / "Dockerfile",
        BUNDLE / ".env.example",
        BUNDLE / "README.md",
        BUNDLE / "requirements.txt",
        BUNDLE / "scripts" / "download_models_to_volume.py",
        ROOT / ".github" / "workflows" / "runpod-s1-model-loader-image.yml",
    ]

    for path in expected:
        assert path.exists(), f"missing loader artifact: {path}"


def test_model_loader_documents_hf_token_and_volume_target() -> None:
    readme = (BUNDLE / "README.md").read_text(encoding="utf-8")
    env_example = (BUNDLE / ".env.example").read_text(encoding="utf-8")
    script = (BUNDLE / "scripts" / "download_models_to_volume.py").read_text(encoding="utf-8")

    assert "HF_TOKEN" in readme
    assert "kl6ru4hrmh" in readme
    assert "RUNPOD_MODELS_ROOT=/runpod-volume/models" in env_example
    assert "black-forest-labs/FLUX.1-schnell" in script
    assert "XLabs-AI/flux-ip-adapter" in script
