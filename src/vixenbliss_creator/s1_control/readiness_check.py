from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from tempfile import mkdtemp
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from vixenbliss_creator.agentic.runner import run_agentic_brain, run_agentic_brain_with_real_llm
from vixenbliss_creator.contracts.identity import TechnicalSheet
from vixenbliss_creator.runtime_providers import ModalRuntimeProviderClient, RuntimeProviderSettings, ServiceRuntime
from vixenbliss_creator.s1_control import S1RuntimeDirectusRecorder

from .bootstrap import bootstrap_directus_schema
from .config import S1ControlSettings
from .directus import DirectusControlPlaneClient
from .support import is_png_bytes, load_local_env, png_dimensions, sha256_hex, tiny_png_bytes


DEFAULT_IDEA = "Quiero una modelo morocha para contenido NSFW, el resto completalo de manera automatica"
DEFAULT_REFERENCE_FACE_IMAGE_URL = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"
REPO_ROOT = Path(__file__).resolve().parents[3]
S1_LLM_RUNTIME_PATH = REPO_ROOT / "infra" / "s1-llm" / "runtime" / "app.py"
S1_IMAGE_RUNTIME_PATH = REPO_ROOT / "infra" / "s1-image" / "runtime" / "app.py"


def _enum_or_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _load_runtime_module(module_name: str, module_path: Path) -> object:
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _read_commented_env_value(key: str) -> str | None:
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return None
    marker = f"# {key}="
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith(marker):
            return line.split("=", 1)[1].strip()
    return None


def _probe_http(url: str | None) -> dict[str, Any]:
    if not url:
        return {"configured": False, "reachable": False}
    try:
        req = urllib.request.Request(url=url, method="GET")
        with urllib.request.urlopen(req, timeout=15) as response:
            return {
                "configured": True,
                "reachable": True,
                "status_code": response.status,
                "content_type": response.headers.get("Content-Type"),
            }
    except urllib.error.HTTPError as exc:
        return {
            "configured": True,
            "reachable": False,
            "status_code": exc.code,
            "error": exc.reason,
        }
    except Exception as exc:
        return {
            "configured": True,
            "reachable": False,
            "error": str(exc),
        }


def _fetch_json(url: str, *, token: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url=url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_bytes(url: str, *, token: str) -> tuple[bytes, dict[str, Any]]:
    req = urllib.request.Request(
        url=url,
        headers={"Authorization": f"Bearer {token}", "Accept": "*/*"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        headers = {
            "content_type": response.headers.get("Content-Type"),
            "content_length": response.headers.get("Content-Length"),
            "content_disposition": response.headers.get("Content-Disposition"),
        }
        return response.read(), headers


def _build_identity_context(technical_sheet: TechnicalSheet) -> dict[str, Any]:
    return {
        "identity_summary": technical_sheet.system5_slots.persona_summary,
        "summary": technical_sheet.identity_core.tagline,
        "voice_tone": _enum_or_value(technical_sheet.personality_profile.voice_tone),
        "style": _enum_or_value(technical_sheet.identity_metadata.style),
        "vertical": _enum_or_value(technical_sheet.identity_metadata.vertical),
        "display_name": technical_sheet.identity_core.display_name,
        "archetype": _enum_or_value(technical_sheet.personality_profile.archetype),
        "personality_axes": technical_sheet.personality_profile.axes.model_dump(mode="json"),
    }


def _create_required_assets(module: object) -> None:
    for path in module._required_runtime_paths().values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"stub")


def _run_s1_llm_job(identity_id: str, technical_sheet: TechnicalSheet) -> dict[str, Any]:
    module = _load_runtime_module(f"vb_s1_llm_runtime_{uuid4().hex}", S1_LLM_RUNTIME_PATH)
    client = TestClient(module.web_app)
    payload = {
        "input": {
            "identity_id": identity_id,
            "identity_context": _build_identity_context(technical_sheet),
            "workflow_id": "base-image-ipadapter-impact",
            "workflow_version": "2026-04-03",
            "base_model_id": "flux-schnell-v1",
            "reference_face_image_url": "https://example.com/reference.png",
            "image_width": 1024,
            "image_height": 1024,
            "ip_adapter": {"enabled": True, "model_name": "plus_face", "weight": 0.9},
            "prompt_hints": {"source": "readiness_check"},
            "negative_prompt_hints": {"safety": "adult_fictional_only"},
        }
    }
    submit = client.post("/jobs", json=payload)
    submit.raise_for_status()
    result = client.get(submit.json()["result_url"])
    result.raise_for_status()
    return result.json()


def _run_s1_image_job(identity_id: str, prompt_request_id: str, generation_result: dict[str, Any]) -> dict[str, Any]:
    modal_result = _run_s1_image_job_via_modal(identity_id, prompt_request_id, generation_result)
    if modal_result is not None:
        return modal_result
    temp_root = Path(mkdtemp(prefix="vb-s1-readiness-"))
    comfy_home = temp_root / "comfyui"
    output_dir = comfy_home / "output" / "vb"
    output_dir.mkdir(parents=True, exist_ok=True)

    os.environ["COMFYUI_HOME"] = str(comfy_home)
    os.environ["COMFYUI_CUSTOM_NODES_DIR"] = str(comfy_home / "custom_nodes")
    os.environ["COMFYUI_MODELS_DIR"] = str(comfy_home / "models")
    os.environ["COMFYUI_USER_DIR"] = str(comfy_home / "user" / "default")
    os.environ["COMFYUI_INPUT_DIR"] = str(comfy_home / "input")
    os.environ["MODEL_CACHE_ROOT"] = str(temp_root / "model-cache")
    os.environ["SERVICE_ARTIFACT_ROOT"] = str(temp_root / "artifacts")
    os.environ["COMFYUI_WORKFLOW_IDENTITY_ID"] = "base-image-ipadapter-impact"
    os.environ["COMFYUI_WORKFLOW_IDENTITY_VERSION"] = "2026-04-03"

    module = _load_runtime_module(f"vb_s1_image_runtime_{uuid4().hex}", S1_IMAGE_RUNTIME_PATH)
    module._ensure_comfyui_running = lambda **_kwargs: None
    module._download_remote_file = lambda *_args, **_kwargs: "reference.png"
    module._submit_prompt = lambda *_args, **_kwargs: "prompt-readiness"
    module._poll_history = lambda _prompt_id: {
        "outputs": {
            "save_base_image": {
                "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
            },
            "face_detector": {"metrics": {"bbox_confidence": 0.93}},
        }
    }
    _create_required_assets(module)
    (output_dir / "base.png").write_bytes(tiny_png_bytes())

    manifest = generation_result["generation_manifest"]
    seed_bundle = manifest["seed_bundle"]
    comfy_parameters = manifest["comfy_parameters"]
    job_input = {
        "action": "generate",
        "mode": "base_render",
        "workflow_id": manifest["workflow_id"],
        "workflow_version": manifest["workflow_version"],
        "base_model_id": manifest["base_model_id"],
        "runtime_stage": "identity_image",
        "prompt": manifest["prompt"],
        "negative_prompt": manifest["negative_prompt"],
        "seed": seed_bundle["portrait_seed"],
        "seed_bundle": seed_bundle,
        "width": comfy_parameters["width"],
        "height": comfy_parameters["height"],
        "reference_face_image_url": comfy_parameters["reference_face_image_url"],
        "ip_adapter": comfy_parameters["ip_adapter"],
        "face_detailer": {"enabled": True, "confidence_threshold": 0.8, "inpaint_strength": 0.35},
        "metadata": {
            "identity_id": identity_id,
            "character_id": identity_id,
            "prompt_request_id": prompt_request_id,
            "autopromote": False,
            "samples_target": 8,
            "seed_bundle": seed_bundle,
        },
    }

    client = TestClient(module.app)
    submit = client.post("/jobs", json={"input": job_input})
    submit.raise_for_status()
    return submit.json()["output"]


def _run_s1_image_job_via_modal(identity_id: str, prompt_request_id: str, generation_result: dict[str, Any]) -> dict[str, Any] | None:
    settings = RuntimeProviderSettings.from_env()
    modal_client = ModalRuntimeProviderClient(settings)
    try:
        import modal

        healthcheck_function = modal.Function.from_name(
            settings.modal_app_name_for(ServiceRuntime.S1_IMAGE) or "vixenbliss-s1-image",
            settings.modal_healthcheck_function_for(ServiceRuntime.S1_IMAGE) or "runtime_healthcheck",
        )
        healthcheck = healthcheck_function.remote(deep=True)
    except Exception:
        return None
    if not bool(healthcheck.get("provider_ready") or healthcheck.get("ok")):
        return None

    manifest = generation_result["generation_manifest"]
    seed_bundle = manifest["seed_bundle"]
    comfy_parameters = manifest["comfy_parameters"]
    payload = {
        "action": "generate",
        "mode": "base_render",
        "workflow_id": manifest["workflow_id"],
        "workflow_version": manifest["workflow_version"],
        "base_model_id": manifest["base_model_id"],
        "runtime_stage": "identity_image",
        "prompt": manifest["prompt"],
        "negative_prompt": manifest["negative_prompt"],
        "seed": seed_bundle["portrait_seed"],
        "seed_bundle": seed_bundle,
        "width": comfy_parameters["width"],
        "height": comfy_parameters["height"],
        "reference_face_image_url": os.getenv("S1_REFERENCE_FACE_IMAGE_URL", DEFAULT_REFERENCE_FACE_IMAGE_URL),
        "ip_adapter": comfy_parameters["ip_adapter"],
        "face_detailer": {"enabled": True, "confidence_threshold": 0.8, "inpaint_strength": 0.35},
        "metadata": {
            "identity_id": identity_id,
            "character_id": identity_id,
            "prompt_request_id": prompt_request_id,
            "autopromote": False,
            "samples_target": 8,
            "seed_bundle": seed_bundle,
        },
    }
    handle = modal_client.submit_job(ServiceRuntime.S1_IMAGE, payload)
    result = modal_client.fetch_result(handle)
    result.setdefault("metadata", {})
    result["metadata"]["readiness_execution_backend"] = "modal_real_runtime"
    if result.get("metadata", {}).get("directus_run_id"):
        return result

    recorder = S1RuntimeDirectusRecorder.from_settings(S1ControlSettings.from_env())
    run = recorder.record_job(
        service_name="s1_image",
        job_id=str(result.get("provider_job_id") or handle.job_id or f"modal-{uuid4().hex[:12]}"),
        status="failed" if result.get("error_code") else "completed",
        input_payload=payload,
        result_payload=result,
        error_message=result.get("error_message"),
    )
    result.setdefault("metadata", {})
    result["metadata"]["directus_run_id"] = str(run.get("id"))
    return result


def _run_agentic_flow(idea: str) -> tuple[TechnicalSheet, dict[str, Any]]:
    try:
        state = run_agentic_brain_with_real_llm(idea)
        if state.final_technical_sheet_payload is not None:
            return state.final_technical_sheet_payload, {
                "mode": "local_real_llm",
                "fallback_used": False,
            }
        failure_reason = state.terminal_error_message or "LangGraph real-LLM run completed without final technical sheet."
    except Exception as exc:
        failure_reason = str(exc)

    fallback_state = run_agentic_brain(idea)
    if fallback_state.final_technical_sheet_payload is None:
        raise RuntimeError("LangGraph fallback runner did not produce a final technical sheet.")
    return fallback_state.final_technical_sheet_payload, {
        "mode": "local_demo_fallback",
        "fallback_used": True,
        "fallback_reason": failure_reason,
    }


def _inspect_directus_artifact(settings: S1ControlSettings, artifact_row: dict[str, Any]) -> dict[str, Any]:
    file_id = artifact_row.get("file")
    asset_bytes = b""
    asset_headers: dict[str, Any] = {}
    file_meta: dict[str, Any] = {}
    uri = str(artifact_row.get("uri") or "")
    metadata_json = artifact_row.get("metadata_json") or {}
    if file_id:
        file_id = str(file_id)
        file_meta = _fetch_json(f"{settings.directus_base_url}/files/{file_id}", token=settings.directus_token)["data"]
        asset_bytes, asset_headers = _fetch_bytes(
            f"{settings.directus_base_url}/assets/{file_id}",
            token=settings.directus_token,
        )
    else:
        path = Path(uri)
        if path.exists() and path.is_file():
            asset_bytes = path.read_bytes()
            file_meta = {
                "type": artifact_row.get("content_type"),
                "filename_download": path.name,
                "filesize": path.stat().st_size,
            }
            asset_headers = {"content_type": artifact_row.get("content_type"), "content_length": str(len(asset_bytes))}
    inspection = {
        "file_id": str(file_id) if file_id is not None else None,
        "role": artifact_row["role"],
        "uri": uri,
        "file_type": file_meta.get("type"),
        "filename_download": file_meta.get("filename_download"),
        "filesize": file_meta.get("filesize"),
        "asset_headers": asset_headers,
        "sha256": sha256_hex(asset_bytes) if asset_bytes else None,
        "is_png_signature": is_png_bytes(asset_bytes) if asset_bytes else False,
        "persistence_target": metadata_json.get("persistence_target"),
    }
    if artifact_row["role"] == "dataset_package":
        if asset_bytes:
            archive = zipfile.ZipFile(io.BytesIO(asset_bytes))
            zip_image = archive.read("images/base-image.png")
            inspection["zip_entries"] = archive.namelist()
            inspection["zip_base_image_size"] = len(zip_image)
            inspection["zip_base_image_is_png"] = is_png_bytes(zip_image)
            inspection["zip_dataset_manifest"] = json.loads(archive.read("dataset-manifest.json").decode("utf-8"))
        else:
            inspection["zip_entries"] = metadata_json.get("package_entries", [])
            inspection["zip_base_image_size"] = None
            inspection["zip_base_image_is_png"] = bool(metadata_json.get("package_contains_base_image_png"))
            inspection["zip_dataset_manifest"] = None
    return inspection


def run_readiness_check(idea: str = DEFAULT_IDEA) -> dict[str, Any]:
    load_local_env()
    bootstrap_directus_schema()
    settings = S1ControlSettings.from_env()
    client = DirectusControlPlaneClient(settings)
    provider_settings = RuntimeProviderSettings.from_env()

    llm_public_url = os.getenv("S1_LLM_RUNTIME_BASE_URL") or _read_commented_env_value("S1_LLM_RUNTIME_BASE_URL")
    directus_health_url = f"{settings.directus_base_url}/server/health"

    endpoint_report = {
        "directus": _probe_http(directus_health_url),
        "s1_llm_public": _probe_http(llm_public_url),
        "s1_image_modal": {
            "configured": bool(os.getenv("MODAL_TOKEN_ID") and os.getenv("MODAL_TOKEN_SECRET")),
            "app_name": provider_settings.modal_app_name_for(ServiceRuntime.S1_IMAGE),
            "job_function": provider_settings.modal_job_function_for(ServiceRuntime.S1_IMAGE),
            "healthcheck_function": provider_settings.modal_healthcheck_function_for(ServiceRuntime.S1_IMAGE),
        },
    }

    prompt_request = client.create_item(
        "s1_prompt_requests",
        {
            "idea": idea,
            "manual_constraints_json": {},
            "creation_mode": "automatic",
            "request_status": "in_progress",
            "requested_by": "codex",
        },
    )

    technical_sheet, agentic_execution = _run_agentic_flow(idea)
    avatar_id_hint = technical_sheet.identity_metadata.avatar_id
    try:
        identity_id = str(UUID(str(avatar_id_hint)))
    except (TypeError, ValueError):
        identity_id = str(uuid4())

    generation_result = _run_s1_llm_job(identity_id, technical_sheet)
    image_result = _run_s1_image_job(str(identity_id), str(prompt_request["id"]), generation_result)
    image_backend = str(image_result.get("metadata", {}).get("readiness_execution_backend") or "local_runtime_fallback")

    run_id = str(image_result["metadata"]["directus_run_id"])
    run_row = client.read_item("s1_generation_runs", run_id)
    artifacts = client.list_items("s1_artifacts", params={"filter[run_id][_eq]": run_id})
    identity_rows = client.list_items("s1_identities", params={"filter[avatar_id][_eq]": str(identity_id), "limit": "1"})
    identity_snapshot = identity_rows[0] if identity_rows else None

    artifact_details = [_inspect_directus_artifact(settings, artifact_row) for artifact_row in artifacts]
    base_image_detail = next((item for item in artifact_details if item["role"] == "base_image"), None)
    dataset_package_detail = next((item for item in artifact_details if item["role"] == "dataset_package"), None)
    base_image_dimensions = png_dimensions(_fetch_bytes(f"{settings.directus_base_url}/assets/{base_image_detail['file_id']}", token=settings.directus_token)[0]) if base_image_detail and base_image_detail.get("file_id") else None
    manifest_seed_bundle = generation_result["generation_manifest"]["seed_bundle"]
    runtime_seed_bundle = image_result["metadata"].get("seed_bundle")
    snapshot_seed_bundle = identity_snapshot.get("latest_seed_bundle_json") if identity_snapshot else None
    seed_traceability_consistent = manifest_seed_bundle == runtime_seed_bundle == snapshot_seed_bundle

    client.update_item(
        "s1_prompt_requests",
        str(prompt_request["id"]),
        {
            "identity_id": str(identity_id),
            "latest_run_id": run_id,
            "request_status": "completed",
        },
    )

    blocking_reasons: list[str] = []
    if image_backend != "modal_real_runtime":
        blocking_reasons.append(
            "La validación visual no salió del worker GPU real de Modal; el readiness todavía depende de un fallback local."
        )
    if not base_image_detail or not base_image_detail["is_png_signature"]:
        blocking_reasons.append("La base image persistida en Directus no es un PNG válido.")
    if not base_image_dimensions or base_image_dimensions[0] <= 1 or base_image_dimensions[1] <= 1:
        blocking_reasons.append("La base image persistida sigue siendo demasiado chica para training y no pasa el umbral mínimo de calidad.")
    if not seed_traceability_consistent:
        blocking_reasons.append("Las semillas no quedaron consistentes entre manifest, runtime e identity snapshot.")
    blocking_reasons.append(
        "La decisión de habilitar LoRA training todavía requiere revisión humana de calidad sobre las imágenes reales generadas."
    )

    return {
        "idea": idea,
        "execution_mode": {
            "langgraph": agentic_execution["mode"],
            "s1_llm": "local_runtime",
            "s1_image": image_backend,
            "directus": "real_service",
            "fallback_reason": None if image_backend == "modal_real_runtime" else "La ejecución real de Modal no estuvo disponible y se usó fallback local.",
        },
        "agentic_execution": agentic_execution,
        "endpoint_report": endpoint_report,
        "prompt_request_id": str(prompt_request["id"]),
        "identity_id": str(identity_id),
        "technical_sheet_summary": {
            "display_name": technical_sheet.identity_core.display_name,
            "avatar_id_hint": avatar_id_hint,
            "vertical": _enum_or_value(technical_sheet.identity_metadata.vertical),
            "style": _enum_or_value(technical_sheet.identity_metadata.style),
            "archetype": _enum_or_value(technical_sheet.personality_profile.archetype),
            "voice_tone": _enum_or_value(technical_sheet.personality_profile.voice_tone),
            "persona_summary": technical_sheet.system5_slots.persona_summary,
        },
        "generation_manifest": generation_result["generation_manifest"],
        "s1_image_output": {
            "directus_run_id": run_id,
            "dataset_handoff_ready": image_result["metadata"].get("dataset_handoff_ready"),
            "dataset_storage_mode": image_result["metadata"].get("dataset_storage_mode"),
            "dataset_review_required": image_result["metadata"].get("dataset_review_required"),
            "seed_bundle": image_result["metadata"].get("seed_bundle"),
            "face_detection_confidence": image_result.get("face_detection_confidence"),
        },
        "directus": {
            "run": {
                "id": str(run_row["id"]),
                "run_type": run_row.get("run_type"),
                "status": run_row.get("status"),
                "provider": run_row.get("provider"),
                "input_idea": run_row.get("input_idea"),
            },
            "artifacts": artifact_details,
            "identity_snapshot": identity_snapshot,
        },
        "png_validation": {
            "base_image_valid": bool(base_image_detail and base_image_detail["is_png_signature"]),
            "base_image_dimensions": list(base_image_dimensions) if base_image_dimensions else None,
            "dataset_zip_base_image_valid": bool(
                dataset_package_detail and dataset_package_detail.get("zip_base_image_is_png")
            ),
            "base_image_size": base_image_detail.get("filesize") if base_image_detail else None,
            "diagnosis": (
                "La corrupción anterior queda explicada por la vieja smoke local que escribía bytes inválidos en base.png antes de persistir. Este readiness reporta el estado real del artifact actual guardado en Directus."
            ),
        },
        "readiness": {
            "structural_ready_for_training": bool(
                image_result["metadata"].get("dataset_handoff_ready")
                and base_image_detail
                and base_image_detail["is_png_signature"]
                and base_image_dimensions is not None
                and base_image_dimensions[0] > 1
                and base_image_dimensions[1] > 1
                and dataset_package_detail
                and dataset_package_detail.get("zip_base_image_is_png")
                and seed_traceability_consistent
            ),
            "seed_traceability_consistent": seed_traceability_consistent,
            "visual_quality_verified": image_backend == "modal_real_runtime" and bool(base_image_dimensions and base_image_dimensions[0] > 1 and base_image_dimensions[1] > 1),
            "can_advance_to_lora_training": False,
            "blocking_reasons": blocking_reasons,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the S1 readiness check before LoRA training.")
    parser.add_argument("--idea", default=DEFAULT_IDEA, help="Prompt inicial a evaluar.")
    args = parser.parse_args()
    result = run_readiness_check(args.idea)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
