from __future__ import annotations

import os
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download
from huggingface_hub.errors import GatedRepoError, HfHubHTTPError


RUNPOD_VOLUME_PATH = Path(os.getenv("RUNPOD_VOLUME_PATH", "/runpod-volume"))
RUNPOD_MODELS_ROOT = Path(os.getenv("RUNPOD_MODELS_ROOT", str(RUNPOD_VOLUME_PATH / "models")))
HF_TOKEN = os.getenv("HF_TOKEN")
FORCE_REDOWNLOAD = os.getenv("FORCE_REDOWNLOAD", "false").lower() in {"1", "true", "yes", "on"}

FLUX_REPO_ID = os.getenv("FLUX_REPO_ID", "black-forest-labs/FLUX.1-schnell")
FLUX_DIFFUSION_FILENAME = os.getenv("FLUX_DIFFUSION_FILENAME", "flux1-schnell.safetensors")
FLUX_AE_FILENAME = os.getenv("FLUX_AE_FILENAME", "ae.safetensors")

FLUX_TEXT_ENCODERS_REPO_ID = os.getenv("FLUX_TEXT_ENCODERS_REPO_ID", "comfyanonymous/flux_text_encoders")
FLUX_CLIP_L_FILENAME = os.getenv("FLUX_CLIP_L_FILENAME", "clip_l.safetensors")
FLUX_T5XXL_FILENAME = os.getenv("FLUX_T5XXL_FILENAME", "t5xxl_fp8_e4m3fn.safetensors")

FLUX_IPADAPTER_REPO_ID = os.getenv("FLUX_IPADAPTER_REPO_ID", "XLabs-AI/flux-ip-adapter")
FLUX_IPADAPTER_SOURCE_FILENAME = os.getenv("FLUX_IPADAPTER_SOURCE_FILENAME", "ip_adapter.safetensors")
FLUX_IPADAPTER_TARGET_FILENAME = os.getenv("FLUX_IPADAPTER_TARGET_FILENAME", "flux-ipadapter-face.safetensors")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def download_file(repo_id: str, filename: str, target: Path, *, token: str | None, gated: bool) -> None:
    ensure_parent(target)
    if target.exists() and not FORCE_REDOWNLOAD:
        print(f"[skip] {target} already exists")
        return

    if gated and not token:
        raise RuntimeError(f"HF_TOKEN is required to download gated model {repo_id}/{filename}")

    try:
        cached = Path(
            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                token=token,
                force_download=FORCE_REDOWNLOAD,
            )
        )
    except GatedRepoError as exc:
        raise RuntimeError(f"Access denied to gated repo {repo_id}. Accept the model terms and use a valid HF_TOKEN.") from exc
    except HfHubHTTPError as exc:
        raise RuntimeError(f"Failed downloading {repo_id}/{filename}: {exc}") from exc

    shutil.copyfile(cached, target)
    print(f"[ok] {repo_id}/{filename} -> {target}")


def main() -> int:
    print(f"[info] writing models into {RUNPOD_MODELS_ROOT}")

    download_file(
        FLUX_REPO_ID,
        FLUX_DIFFUSION_FILENAME,
        RUNPOD_MODELS_ROOT / "diffusion_models" / FLUX_DIFFUSION_FILENAME,
        token=HF_TOKEN,
        gated=True,
    )
    download_file(
        FLUX_REPO_ID,
        FLUX_AE_FILENAME,
        RUNPOD_MODELS_ROOT / "vae" / FLUX_AE_FILENAME,
        token=HF_TOKEN,
        gated=True,
    )
    download_file(
        FLUX_TEXT_ENCODERS_REPO_ID,
        FLUX_CLIP_L_FILENAME,
        RUNPOD_MODELS_ROOT / "text_encoders" / FLUX_CLIP_L_FILENAME,
        token=HF_TOKEN,
        gated=False,
    )
    download_file(
        FLUX_TEXT_ENCODERS_REPO_ID,
        FLUX_T5XXL_FILENAME,
        RUNPOD_MODELS_ROOT / "text_encoders" / FLUX_T5XXL_FILENAME,
        token=HF_TOKEN,
        gated=False,
    )
    download_file(
        FLUX_IPADAPTER_REPO_ID,
        FLUX_IPADAPTER_SOURCE_FILENAME,
        RUNPOD_MODELS_ROOT / "ipadapter-flux" / FLUX_IPADAPTER_TARGET_FILENAME,
        token=HF_TOKEN,
        gated=False,
    )

    print("[done] S1 model volume is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
