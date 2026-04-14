from __future__ import annotations

import base64
import importlib.util
import json
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from fastapi.testclient import TestClient

from vixenbliss_creator.s1_control.support import tiny_png_bytes

try:
    import modal
except ImportError:  # pragma: no cover - local fallback for contract tests without the modal package
    class _ModalFunctionStub:
        @staticmethod
        def from_name(*_args, **_kwargs):
            raise RuntimeError("modal package is not installed")

    class _ModalStub:
        Function = _ModalFunctionStub

    modal = _ModalStub()
    sys.modules.setdefault("modal", modal)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "infra" / "s1-image" / "runtime" / "app.py"


def _load_runtime_module(tmp_path: Path, monkeypatch) -> object:
    comfy_home = tmp_path / "comfyui"
    models_dir = comfy_home / "models"
    output_dir = comfy_home / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("COMFYUI_HOME", str(comfy_home))
    monkeypatch.setenv("COMFYUI_CUSTOM_NODES_DIR", str(comfy_home / "custom_nodes"))
    monkeypatch.setenv("COMFYUI_MODELS_DIR", str(models_dir))
    monkeypatch.setenv("COMFYUI_USER_DIR", str(comfy_home / "user" / "default"))
    monkeypatch.setenv("COMFYUI_INPUT_DIR", str(comfy_home / "input"))
    monkeypatch.setenv("MODEL_CACHE_ROOT", str(tmp_path / "model-cache"))
    monkeypatch.setenv("DIRECTUS_BASE_URL", "http://example.com")
    monkeypatch.setenv("DIRECTUS_API_TOKEN", "secret")

    spec = importlib.util.spec_from_file_location("test_s1_image_runtime_module", RUNTIME_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["test_s1_image_runtime_module"] = module
    spec.loader.exec_module(module)
    return module


def _create_required_flux_assets(module: object, job_input: dict | None = None) -> None:
    for path in module._required_runtime_paths(job_input).values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"stub")


def _base_job_input(**overrides: object) -> dict:
    payload = {
        "action": "generate",
        "mode": "base_render",
        "workflow_id": "base-image-ipadapter-impact",
        "workflow_version": "2026-03-31",
        "base_model_id": "flux-schnell-v1",
        "runtime_stage": "identity_image",
        "prompt": "editorial portrait of a synthetic premium performer",
        "negative_prompt": "low quality, anatomy drift, extra limbs, text, watermark",
        "seed": 42,
        "width": 1024,
        "height": 1024,
        "reference_face_image_url": "https://example.com/ref.png",
        "ip_adapter": {"enabled": True, "model_name": "plus_face", "weight": 0.9},
        "face_detailer": {"enabled": True, "confidence_threshold": 0.8, "inpaint_strength": 0.35},
    }
    payload.update(overrides)
    return payload


def _install_sequential_dataset_renderer(module: object) -> None:
    prompt_counter = {"value": 0}

    def fake_submit_prompt(*_args, **_kwargs) -> str:
        prompt_counter["value"] += 1
        return f"prompt-{prompt_counter['value']}"

    def fake_poll_history(prompt_id: str) -> dict:
        prompt_number = int(prompt_id.split("-")[-1])
        filename = f"sample-{prompt_number:03d}.png" if prompt_number > 1 else "base.png"
        (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / filename).write_bytes(tiny_png_bytes() + prompt_id.encode("ascii"))
        return {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": filename, "subfolder": "vb", "type": "output"}],
                },
                "face_detector": {"metrics": {"bbox_confidence": 0.91}},
            }
        }

    module._submit_prompt = fake_submit_prompt
    module._poll_history = fake_poll_history


def _authenticate_test_client(module: object, client: TestClient) -> None:
    module._directus_login = lambda email, password: {"access_token": f"token-for-{email}"}
    module._directus_me = lambda access_token: {
        "id": "user-1",
        "email": "operator@vixenbliss.local",
        "first_name": "Vixen",
        "last_name": "Operator",
        "status": "active",
    }
    response = client.post("/auth/login", json={"email": "operator@vixenbliss.local", "password": "secret"})
    assert response.status_code == 200


def _ready_lab_session(client: TestClient, session_id: str) -> dict:
    first = client.post(
        "/lab/chat",
        json={
            "session_id": session_id,
            "message": "Quiero una modelo de 40 años, licenciada en psicologia, crea contenido NSFW en su estudio, es formal.",
        },
    )
    assert first.status_code == 200
    second = client.post(
        "/lab/chat",
        json={"session_id": session_id, "message": "quiero que tenga ojos verdes y que sea rubia"},
    )
    assert second.status_code == 200
    return second.json()


def test_s1_image_runtime_healthcheck_reports_identity_contract(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_healthcheck", lambda timeout_seconds=2: True)
    _create_required_flux_assets(module, _base_job_input())
    client = TestClient(module.app)

    response = client.get("/healthcheck")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["runtime_contract"]["runtime_stage"] == "identity_image"
    assert payload["runtime_contract"]["workflow_scope"] == "s1_image"
    assert payload["runtime_contract"]["lora_supported"] is False


def test_s1_image_runtime_root_page_renders_chat_layout(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)

    response = client.get("/")

    assert response.status_code == 200
    assert "VixenBliss Creator" in response.text
    assert "Internal access" in response.text
    assert '"routeMode": "login"' in response.text


def test_s1_image_runtime_serves_web_assets_from_monorepo_app(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)

    response = client.get("/web/assets/app.js")

    assert response.status_code == 200
    assert "handleHandoff" in response.text
    assert "buildSessionId" in response.text
    assert "defaultReferenceFaceImageUrl" in client.get("/").text


def test_s1_image_runtime_can_resolve_web_root_from_override(tmp_path: Path, monkeypatch) -> None:
    public_root = tmp_path / "custom-web" / "public"
    assets_root = public_root / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    (public_root / "index.html").write_text("<html><body>__VB_WEB_CONFIG__</body></html>", encoding="utf-8")
    (assets_root / "app.js").write_text("console.log('override');", encoding="utf-8")
    monkeypatch.setenv("VB_WEB_PUBLIC_ROOT", str(public_root))

    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)

    root = client.get("/")
    asset = client.get("/web/assets/app.js")

    assert root.status_code == 200
    assert "__VB_WEB_CONFIG__" not in root.text
    assert asset.status_code == 200
    assert "override" in asset.text


def test_s1_image_runtime_auth_login_sets_session_cookie(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)

    _authenticate_test_client(module, client)

    session_response = client.get("/auth/session")

    assert session_response.status_code == 200
    assert session_response.json()["authenticated"] is True
    assert session_response.json()["user"]["email"] == "operator@vixenbliss.local"


def test_s1_image_runtime_auth_rejects_invalid_credentials(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    module._directus_login = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("invalid credentials"))

    response = client.post("/auth/login", json={"email": "operator@vixenbliss.local", "password": "bad"})

    assert response.status_code == 401
    assert "Directus login failed" in response.json()["detail"]


def test_s1_image_runtime_lab_endpoints_require_auth(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)

    response = client.post("/lab/chat", json={"session_id": "session-auth", "message": "hola"})

    assert response.status_code == 401


def test_s1_image_runtime_uploaded_reference_takes_priority_over_url(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    _authenticate_test_client(module, client)
    captured: dict[str, object] = {}

    def fake_submit_job(payload: dict) -> dict:
        captured["payload"] = payload
        return {
            "job_id": "job-file-ref",
            "status": "completed",
            "result_url": "/jobs/job-file-ref/result",
            "progress_url": "/ws/jobs/job-file-ref",
            "metadata": {"progress_events": []},
        }

    monkeypatch.setattr(module, "submit_job", fake_submit_job)

    upload = client.post(
        "/lab/reference-uploads",
        json={
            "session_id": "session-file-ref",
            "filename": "face.png",
            "content_type": "image/png",
            "data_base64": base64.b64encode(tiny_png_bytes()).decode("ascii"),
        },
    )
    assert upload.status_code == 200

    ready_payload = _ready_lab_session(client, "session-file-ref")
    assert ready_payload["can_handoff"] is True

    response = client.post(
        "/lab/s1-image",
        json={"session_id": "session-file-ref", "reference_face_image_url": "https://example.com/custom.png"},
    )

    assert response.status_code == 200
    assert "reference-files" in captured["payload"]["input"]["reference_face_image_url"]
    assert response.json()["handoff"]["reference_face_source"] == "file"


def test_s1_image_runtime_uploaded_reference_file_requires_auth(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    _authenticate_test_client(module, client)

    upload = client.post(
        "/lab/reference-uploads",
        json={
            "session_id": "session-protected-file",
            "filename": "face.png",
            "content_type": "image/png",
            "data_base64": base64.b64encode(tiny_png_bytes()).decode("ascii"),
        },
    )
    assert upload.status_code == 200

    reference_url = upload.json()["reference"]["effective_url"]
    protected_path = reference_url.replace("http://testserver", "")

    authed_fetch = client.get(protected_path)
    assert authed_fetch.status_code == 200

    client.post("/auth/logout", json={})
    unauthed_fetch = client.get(protected_path)
    assert unauthed_fetch.status_code == 401


def test_s1_image_runtime_lab_executes_langgraph_and_returns_panel(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    _authenticate_test_client(module, client)

    response = client.post(
        "/lab/chat",
        json={
            "session_id": "session-1",
            "message": "Quiero una modelo de 40 años, licenciada en psicologia, crea contenido NSFW en su estudio, es formal.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "session-1"
    assert payload["chat_entry"]["status"] == "succeeded"
    assert payload["can_handoff"] is False
    assert payload["panel"]["identity"]["display_name"] != "Velvet Ember"
    assert payload["panel"]["copilot"]["workflow_id"] == "lora-dataset-ipadapter-batch"
    assert payload["panel"]["traceability"]["missing_fields"] == ["visual_profile.eye_color", "visual_profile.hair_color"]
    assert payload["panel"]["traceability"]["missing_field_labels"] == ["Eye color", "Hair color"]
    assert "S1 Image" in payload["chat_entry"]["assistant_message"]
    assert "Eye color" in payload["chat_entry"]["assistant_message"]
    assert payload["panel"]["s1_payload_preview"]["reference_face_image_url"] is None


def test_s1_image_runtime_lab_localizes_chat_panel_to_spanish_when_requested(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    _authenticate_test_client(module, client)

    response = client.post(
        "/lab/chat",
        json={
            "session_id": "session-es",
            "locale": "es-AR",
            "message": "Quiero una modelo de 40 años, licenciada en psicologia, crea contenido NSFW en su estudio, es formal.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["panel"]["traceability"]["missing_field_labels"] == ["Color de ojos", "Color de pelo"]
    assert "Color de ojos" in payload["chat_entry"]["assistant_message"]
    assert "Todavia no esta lista para S1 Image" in payload["chat_entry"]["assistant_message"]


def test_s1_image_runtime_lab_chat_overwrites_visual_fields_and_trims_trace_sources(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    _authenticate_test_client(module, client)

    first = client.post(
        "/lab/chat",
        json={
            "session_id": "session-overwrite",
            "message": "Quiero una modelo de 40 años, licenciada en psicologia, crea contenido NSFW en su estudio, es formal.",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/lab/chat",
        json={"session_id": "session-overwrite", "message": "quiero que tenga ojos verdes y que sea rubia"},
    )

    assert second.status_code == 200
    payload = second.json()
    assert payload["can_handoff"] is True
    assert payload["panel"]["visual_profile"]["eyes"] == "green"
    assert payload["panel"]["visual_profile"]["hair"].startswith("blonde")
    eye_trace = payload["panel"]["traceability"]["field_traces"]["visual_profile.eye_color"]
    hair_trace = payload["panel"]["traceability"]["field_traces"]["visual_profile.hair_color"]
    assert eye_trace["origin"] == "manual"
    assert hair_trace["origin"] == "manual"
    assert len(eye_trace["source_text"]) <= 200
    assert len(hair_trace["source_text"]) <= 200


def test_s1_image_runtime_lab_handoff_uses_graph_state_readiness(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    _authenticate_test_client(module, client)

    first = client.post(
        "/lab/chat",
        json={
            "session_id": "session-incomplete",
            "message": "Quiero una modelo de 40 años, licenciada en psicologia, crea contenido NSFW en su estudio, es formal.",
        },
    )
    assert first.status_code == 200
    assert first.json()["can_handoff"] is False

    response = client.post(
        "/lab/s1-image",
        json={"session_id": "session-incomplete", "reference_face_image_url": "https://cdn.vixenbliss.local/custom.png"},
    )

    assert response.status_code == 409
    assert "Eye color" in response.json()["detail"]


def test_s1_image_runtime_lab_follow_up_turns_keep_prior_operator_constraints(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    _authenticate_test_client(module, client)
    real_runner = module.run_agentic_brain
    captured_ideas: list[str] = []

    def fake_run_agentic_brain(idea: str):
        captured_ideas.append(idea)
        return real_runner(idea)

    monkeypatch.setattr(module, "run_agentic_brain", fake_run_agentic_brain)

    first = client.post(
        "/lab/chat",
        json={
            "session_id": "session-context",
            "message": "Quiero un avatar llamada Luna, estilo glam y piel oliva para lifestyle premium.",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/lab/chat",
        json={"session_id": "session-context", "message": "ahora quiero que tenga ojos verdes"},
    )

    assert second.status_code == 200
    assert len(captured_ideas) == 2
    assert "Luna" in captured_ideas[1]
    assert "glam" in captured_ideas[1].lower()
    assert "piel oliva" in captured_ideas[1].lower()
    assert "ojos verdes" in captured_ideas[1].lower()


def test_s1_image_runtime_lab_chat_applies_display_name_override(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    _authenticate_test_client(module, client)

    ready_payload = _ready_lab_session(client, "session-rename")
    previous_name = ready_payload["panel"]["identity"]["display_name"]
    assert previous_name

    response = client.post(
        "/lab/chat",
        json={"session_id": "session-rename", "message": "Cambiemos el nomrbe a Julia Risitos"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["panel"]["identity"]["display_name"] != previous_name
    assert payload["panel"]["identity"]["display_name"] == "Julia Risitos"
    assert payload["panel"]["identity_context"]["display_name"] == "Julia Risitos"
    assert payload["panel"]["s1_payload_preview"]["metadata"]["identity_context"]["display_name"] == "Julia Risitos"
    assert "Julia Risitos" in payload["chat_entry"]["assistant_message"]
    assistant_message = payload["chat_entry"]["assistant_message"]
    assert ("name: Julia Risitos" in assistant_message) or ("nombre: Julia Risitos" in assistant_message)


def test_s1_image_runtime_lab_autofill_can_complete_remaining_fields(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    _authenticate_test_client(module, client)

    first = client.post(
        "/lab/chat",
        json={"session_id": "session-autofill", "message": "Quiero una modelo de 40 años y que sea formal."},
    )
    assert first.status_code == 200
    assert first.json()["can_handoff"] is False

    second = client.post(
        "/lab/chat",
        json={"session_id": "session-autofill", "message": "completá el resto automáticamente"},
    )

    assert second.status_code == 200
    payload = second.json()
    assert payload["can_handoff"] is True
    assert payload["panel"]["readiness"]["can_handoff"] is True
    assert payload["panel"]["readiness"]["missing_fields"] == []
    assert payload["panel"]["readiness"]["missing_field_labels"] == []


def test_s1_image_runtime_lab_returns_controlled_error_when_langgraph_fails(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "run_agentic_brain", lambda _idea: (_ for _ in ()).throw(RuntimeError("runner exploded")))
    client = TestClient(module.app)
    _authenticate_test_client(module, client)

    response = client.post("/lab/langgraph", json={"session_id": "session-2", "idea": "Probar fallo"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["chat_entry"]["status"] == "failed"
    assert payload["chat_entry"]["error"] == "runner exploded"
    assert payload["can_handoff"] is False


def test_s1_image_runtime_lab_handoff_builds_job_payload_and_reuses_jobs_flow(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    _authenticate_test_client(module, client)
    captured: dict[str, object] = {}

    def fake_submit_job(payload: dict) -> dict:
        captured["payload"] = payload
        return {
            "job_id": "job-lab-123",
            "status": "completed",
            "result_url": "/jobs/job-lab-123/result",
            "progress_url": "/ws/jobs/job-lab-123",
            "metadata": {"progress_events": []},
        }

    monkeypatch.setattr(module, "submit_job", fake_submit_job)

    ready_payload = _ready_lab_session(client, "session-3")
    assert ready_payload["can_handoff"] is True

    response = client.post(
        "/lab/s1-image",
        json={"session_id": "session-3", "reference_face_image_url": "https://cdn.vixenbliss.local/custom.png"},
    )

    assert response.status_code == 200
    payload = response.json()
    job_input = captured["payload"]["input"]
    assert job_input["runtime_stage"] == "identity_image"
    assert job_input["workflow_id"] == "lora-dataset-ipadapter-batch"
    assert job_input["reference_face_image_url"] == "https://cdn.vixenbliss.local/custom.png"
    assert job_input["metadata"]["source_mode"] == "langgraph_lab"
    assert payload["handoff"]["job"]["job_id"] == "job-lab-123"
    assert payload["panel"]["s1_payload_preview"]["reference_face_image_url"] == "https://cdn.vixenbliss.local/custom.png"


def test_s1_image_runtime_lab_handoff_requires_succeeded_graph_state(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    _authenticate_test_client(module, client)

    response = client.post("/lab/s1-image", json={"session_id": "missing-session"})

    assert response.status_code == 409
    assert "There is no previous LangGraph run" in response.json()["detail"]


def test_s1_image_runtime_resolves_plus_face_to_ip_adapter_bin(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)

    assert module._resolve_ip_adapter_model_name({"ip_adapter": {"model_name": "plus_face"}}) == "ip-adapter.bin"
    assert (
        module._cache_runtime_paths(
            {"reference_face_image_url": "https://example.com/ref.png", "ip_adapter": {"model_name": "plus_face"}}
        )["ip_adapter_flux"].name
        == "ip-adapter.bin"
    )


def test_s1_image_runtime_reports_reference_image_not_found(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError("reference_face_image_url could not be resolved")))
    _create_required_flux_assets(module, _base_job_input())
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input()})
    assert submit.status_code == 200
    assert submit.json()["status"] == "failed"
    progress_stages = [event["stage"] for event in submit.json()["metadata"]["progress_events"]]
    assert progress_stages[-1] == "failed"
    result = client.get(submit.json()["result_url"])

    assert result.status_code == 200
    assert result.json()["error_code"] == "REFERENCE_IMAGE_NOT_FOUND"


def test_s1_image_runtime_rejects_non_identity_stage(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    _create_required_flux_assets(module, _base_job_input())
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input(runtime_stage="content_image")})
    result = client.get(submit.json()["result_url"])

    assert result.json()["error_code"] == "COMFYUI_EXECUTION_FAILED"
    assert "unsupported runtime_stage content_image" in result.json()["error_message"]


def test_s1_image_runtime_rejects_lora_usage(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    _create_required_flux_assets(module, _base_job_input())
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input(lora_version="amber-v1")})
    result = client.get(submit.json()["result_url"])

    assert result.json()["error_code"] == "COMFYUI_EXECUTION_FAILED"
    assert "must not consume a LoRA version" in result.json()["error_message"]


def test_s1_image_runtime_reports_missing_artifacts_as_execution_failure(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    monkeypatch.setattr(module, "_submit_prompt", lambda *_args, **_kwargs: "prompt-1")
    monkeypatch.setattr(
        module,
        "_poll_history",
        lambda _prompt_id: {"outputs": {}},
    )
    _create_required_flux_assets(module, _base_job_input())
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input()})
    result = client.get(submit.json()["result_url"])

    assert result.json()["error_code"] == "COMFYUI_EXECUTION_FAILED"


def test_s1_image_runtime_infers_face_confidence_when_detector_output_has_no_metric(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    monkeypatch.setattr(module, "_submit_prompt", lambda *_args, **_kwargs: "prompt-1")
    monkeypatch.setattr(
        module,
        "_poll_history",
        lambda _prompt_id: {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
                },
                "face_detector": {"detections": [{"label": "face"}]},
            }
        },
    )
    _create_required_flux_assets(module, _base_job_input())
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(tiny_png_bytes())
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input()})
    result = client.get(submit.json()["result_url"])
    payload = result.json()

    assert payload.get("error_code") is None
    assert payload["face_detection_confidence"] == 0.8
    assert payload["metadata"]["face_detection_confidence_inferred"] is True


def test_s1_image_runtime_base_render_exposes_checkpoint_and_progress(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    monkeypatch.setattr(module, "_submit_prompt", lambda *_args, **_kwargs: "prompt-1")
    monkeypatch.setattr(
        module,
        "_poll_history",
        lambda _prompt_id: {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
                },
                "face_detector": {"metrics": {"bbox_confidence": 0.61}},
            }
        },
    )
    _create_required_flux_assets(module, _base_job_input(mode="face_detail"))
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(tiny_png_bytes())
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input()})
    assert submit.status_code == 200
    assert submit.json()["progress_url"].endswith("/ws/jobs/" + submit.json()["job_id"])
    assert submit.json()["output"]["provider"] == "modal"
    result = client.get(submit.json()["result_url"])

    payload = result.json()
    assert payload["provider"] == "modal"
    assert payload["face_detection_confidence"] == 0.61
    assert payload["artifacts"][0]["role"] == "base_image"
    assert payload["resume_checkpoint"]["stage"] == "base_render"
    assert payload["resume_checkpoint"]["intermediate_artifacts"][0]["role"] == "base_image"
    progress_stages = [event["stage"] for event in submit.json()["metadata"]["progress_events"]]
    assert "building_workflow" in progress_stages
    assert "submitting_prompt" in progress_stages
    assert "base_render_complete" in progress_stages


def test_s1_image_runtime_builds_base_render_without_reference_image(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)

    workflow = module._build_workflow_payload(_base_job_input(reference_face_image_url=None))

    assert workflow["sampler_scheduler"]["inputs"]["model"] == ["model_sampling_flux", 0]
    assert workflow["basic_guider"]["inputs"]["model"] == ["model_sampling_flux", 0]
    assert workflow["face_detailer"]["inputs"]["model"] == ["model_sampling_flux", 0]


def test_s1_image_runtime_skips_reference_assets_when_job_has_no_reference(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)

    job_input = _base_job_input(reference_face_image_url=None, ip_adapter={"enabled": False, "model_name": "plus_face", "weight": 0.9})
    runtime_paths = module._required_runtime_paths(job_input)
    runtime_checks = module._runtime_checks(job_input)

    _create_required_flux_assets(module, job_input)

    assert "ip_adapter_flux" not in runtime_paths
    assert runtime_checks["ip_adapter_present"] is True
    assert runtime_checks["clip_vision_present"] is True
    module._assert_required_runtime_inputs(job_input)


def test_s1_image_runtime_base_render_without_reference_does_not_require_ip_adapter_assets(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_submit_prompt", lambda *_args, **_kwargs: "prompt-1")
    monkeypatch.setattr(
        module,
        "_poll_history",
        lambda _prompt_id: {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
                },
                "face_detector": {"metrics": {"bbox_confidence": 0.72}},
            }
        },
    )
    for key, path in module._required_runtime_paths(_base_job_input(reference_face_image_url=None, ip_adapter={"enabled": False})).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"stub")
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(tiny_png_bytes())
    client = TestClient(module.app)

    submit = client.post(
        "/jobs",
        json={"input": _base_job_input(reference_face_image_url=None, ip_adapter={"enabled": False, "model_name": "plus_face", "weight": 0.9})},
    )
    result = client.get(submit.json()["result_url"])
    payload = result.json()

    assert payload.get("error_code") is None
    assert payload["face_detection_confidence"] == 0.72
    assert payload["ip_adapter_used"] is False


def test_s1_image_runtime_materializes_dataset_handoff_when_identity_id_is_present(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    _install_sequential_dataset_renderer(module)
    _create_required_flux_assets(module, _base_job_input())
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(tiny_png_bytes())
    client = TestClient(module.app)

    identity_id = str(uuid4())
    submit = client.post(
        "/jobs",
        json={
            "input": _base_job_input(
                seed_bundle={"portrait_seed": 42, "variation_seed": 84, "dataset_seed": 126},
                metadata={
                    "identity_id": identity_id,
                    "character_id": identity_id,
                    "autopromote": True,
                    "samples_target": 40,
                },
                workflow_family="flux_lora_dataset_reference",
                workflow_registry_source="demo_runner",
            )
        },
    )
    payload = submit.json()["output"]

    assert payload["metadata"]["dataset_handoff_ready"] is True
    assert payload["metadata"]["dataset_review_required"] is False
    assert payload["metadata"]["dataset_storage_mode"] == "local_artifact_root"
    assert payload["metadata"]["persisted_artifacts"] == []
    assert payload["metadata"]["dataset_version"].startswith("dataset-")
    assert payload["metadata"]["render_samples_target"] == 80
    assert payload["metadata"]["selection_policy"] == "score_curated_v1"
    assert payload["metadata"]["dataset_composition"] == {
        "policy": "balanced_50_50_curated",
        "SFW": 20,
        "NSFW": 20,
    }
    assert payload["metadata"]["seed"] == 42
    assert payload["metadata"]["seed_bundle"]["portrait_seed"] == 42
    assert payload["metadata"]["seed_bundle"]["variation_seed"] == 84
    assert payload["metadata"]["seed_bundle"]["dataset_seed"] == 126
    assert payload["metadata"]["character_id"] == identity_id
    assert payload["metadata"]["workflow_id"] == "base-image-ipadapter-impact"
    assert payload["metadata"]["workflow_family"] == "flux_lora_dataset_reference"
    assert payload["metadata"]["workflow_registry_source"] == "demo_runner"
    assert payload["metadata"]["base_model_id"] == "flux-schnell-v1"
    assert payload["dataset_manifest"]["identity_id"] == identity_id
    assert payload["dataset_manifest"]["character_id"] == identity_id
    assert payload["dataset_manifest"]["sample_count"] == 40
    assert payload["dataset_manifest"]["generated_samples"] == 40
    assert payload["dataset_manifest"]["render_sample_count"] == 80
    assert payload["dataset_manifest"]["selected_sample_count"] == 40
    assert payload["dataset_manifest"]["workflow_family"] == "flux_lora_dataset_reference"
    assert payload["dataset_manifest"]["workflow_registry_source"] == "demo_runner"
    assert payload["dataset_manifest"]["composition"] == {
        "policy": "balanced_50_50_curated",
        "SFW": 20,
        "NSFW": 20,
    }
    assert len(payload["dataset_manifest"]["files"]) == 40
    assert len(payload["dataset_manifest"]["render_files"]) == 80
    assert payload["dataset_manifest"]["files"][0]["path"].startswith("images/SFW/")
    assert payload["dataset_manifest"]["render_files"][-1]["path"].startswith("images/SFW/") or payload["dataset_manifest"]["render_files"][-1]["path"].startswith("images/NSFW/")
    assert payload["dataset_manifest"]["files"][0]["camera_angle"] in {"front", "left_three_quarter", "right_three_quarter", "left_profile", "right_profile"}
    assert payload["dataset_manifest"]["files"][0]["framing"] in {"close_up_face", "medium", "full_body"}
    assert payload["dataset_manifest"]["files"][0]["camera_distance"] in {"tight_portrait", "editorial_mid", "wide_full_body"}
    assert payload["dataset_manifest"]["files"][0]["prompt"].startswith("editorial portrait")
    assert payload["dataset_manifest"]["files"][0]["byte_size"] > 0
    assert payload["dataset_manifest"]["selection_policy"] == "score_curated_v1"
    assert len(payload["dataset_manifest"]["rejected_sample_ids"]) == 40
    assert payload["generation_manifest"]["seed_bundle"]["portrait_seed"] == 42
    assert payload["generation_manifest"]["seed_bundle"]["variation_seed"] == 84
    assert payload["generation_manifest"]["seed_bundle"]["dataset_seed"] == 126
    assert payload["generation_manifest"]["render_samples_target"] == 80
    assert Path(payload["dataset_manifest"]["artifact_path"]).exists()
    assert Path(payload["dataset_package_path"]).exists()
    assert Path(payload["metadata"]["render_package_path"]).exists()
    assert {artifact["artifact_type"] for artifact in payload["dataset_artifacts"]} == {
        "base_image",
        "dataset_manifest",
        "dataset_package",
    }
    base_image_artifact = next(item for item in payload["dataset_artifacts"] if item["artifact_type"] == "base_image")
    assert base_image_artifact["metadata_json"]["character_id"] == identity_id
    assert isinstance(base_image_artifact["metadata_json"]["inline_data_base64"], str)
    manifest_payload = json.loads(Path(payload["dataset_manifest"]["artifact_path"]).read_text(encoding="utf-8"))
    assert manifest_payload["checksum_sha256"] == payload["dataset_manifest"]["checksum_sha256"]
    with zipfile.ZipFile(payload["dataset_package_path"]) as archive:
        archive_names = set(archive.namelist())
        sample_payloads = {archive.read(file_entry["path"]) for file_entry in payload["dataset_manifest"]["files"]}
    assert "dataset-manifest.json" in archive_names
    assert len([name for name in archive_names if name.endswith(".png") and name.startswith("images/")]) == 40
    assert len(sample_payloads) == 40


def test_s1_image_runtime_uses_selected_workflow_template_from_job_input(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    captured: dict[str, object] = {}

    def fake_submit_prompt(workflow: dict, *, mode: str, job_input: dict | None = None) -> str:
        captured["workflow_keys"] = sorted(workflow.keys())
        captured["extra_workflow_id"] = job_input["workflow_id"] if job_input is not None else None
        captured["extra_workflow_version"] = job_input["workflow_version"] if job_input is not None else None
        return "prompt-variant"

    monkeypatch.setattr(module, "_submit_prompt", fake_submit_prompt)
    monkeypatch.setattr(
        module,
        "_poll_history",
        lambda _prompt_id: {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
                },
                "face_detector": {"metrics": {"bbox_confidence": 0.84}},
            }
        },
    )
    _create_required_flux_assets(module, _base_job_input())
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(tiny_png_bytes())
    client = TestClient(module.app)

    submit = client.post(
        "/jobs",
        json={
            "input": _base_job_input(
                workflow_id="lora-dataset-ipadapter-batch",
                workflow_version="2026-04-08",
                workflow_family="flux_lora_dataset_reference",
                workflow_registry_source="approved_internal_fallback",
            )
        },
    )
    payload = submit.json()["output"]

    assert "load_diffusion_model" in captured["workflow_keys"]
    assert captured["extra_workflow_id"] == "lora-dataset-ipadapter-batch"
    assert captured["extra_workflow_version"] == "2026-04-08"
    assert payload["workflow_id"] == "lora-dataset-ipadapter-batch"
    assert payload["workflow_version"] == "2026-04-08"
    assert payload["metadata"]["workflow_family"] == "flux_lora_dataset_reference"
    assert payload["metadata"]["workflow_registry_source"] == "approved_internal_fallback"


def test_s1_image_runtime_response_includes_directus_persistence_metadata(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    _install_sequential_dataset_renderer(module)
    _create_required_flux_assets(module, _base_job_input())
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(tiny_png_bytes())

    class FakeRecorder:
        def record_job(self, **kwargs) -> dict:
            result_payload = kwargs["result_payload"]
            result_payload["metadata"]["dataset_storage_mode"] = "directus_files"
            result_payload["metadata"]["persisted_artifacts"] = [{"role": "base_image", "file_id": "file-123"}]
            return {"id": "run-123"}

    module._directus_recorder = FakeRecorder()
    client = TestClient(module.app)

    identity_id = str(uuid4())
    response = client.post(
        "/jobs",
        json={"input": _base_job_input(metadata={"identity_id": identity_id, "autopromote": True, "samples_target": 40})},
    )
    payload = response.json()["output"]

    assert payload["metadata"]["dataset_storage_mode"] == "directus_files"
    assert payload["metadata"]["directus_run_id"] == "run-123"
    assert payload["metadata"]["persisted_artifacts"][0]["file_id"] == "file-123"


def test_s1_image_runtime_exposes_directus_recording_failure(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    _install_sequential_dataset_renderer(module)
    _create_required_flux_assets(module, _base_job_input())
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(tiny_png_bytes())

    class FailingRecorder:
        def record_job(self, **kwargs) -> dict:
            raise RuntimeError("directus unavailable")

    module._directus_recorder = FailingRecorder()
    client = TestClient(module.app)
    identity_id = str(uuid4())

    response = client.post(
        "/jobs",
        json={"input": _base_job_input(metadata={"identity_id": identity_id, "autopromote": True, "samples_target": 40})},
    )
    payload = response.json()["output"]

    assert payload["metadata"]["directus_recording_failed"] is True
    assert "directus unavailable" in payload["metadata"]["directus_recording_error"]


def test_s1_image_runtime_skips_dataset_handoff_without_identity_id(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    monkeypatch.setattr(module, "_submit_prompt", lambda *_args, **_kwargs: "prompt-1")
    monkeypatch.setattr(
        module,
        "_poll_history",
        lambda _prompt_id: {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
                },
                "face_detector": {"metrics": {"bbox_confidence": 0.88}},
            }
        },
    )
    _create_required_flux_assets(module, _base_job_input())
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(tiny_png_bytes())
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input()})
    payload = submit.json()["output"]

    assert payload["metadata"]["dataset_handoff_ready"] is False
    assert "dataset_manifest" not in payload


def test_s1_image_runtime_fails_dataset_builder_when_balance_cannot_be_satisfied(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    monkeypatch.setattr(module, "_submit_prompt", lambda *_args, **_kwargs: "prompt-1")
    monkeypatch.setattr(
        module,
        "_poll_history",
        lambda _prompt_id: {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
                },
                "face_detector": {"metrics": {"bbox_confidence": 0.88}},
            }
        },
    )
    _create_required_flux_assets(module, _base_job_input())
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(tiny_png_bytes())
    client = TestClient(module.app)

    submit = client.post(
        "/jobs",
        json={"input": _base_job_input(metadata={"identity_id": str(uuid4()), "samples_target": 7})},
    )
    payload = submit.json()["output"]

    assert payload["error_code"] == "COMFYUI_EXECUTION_FAILED"
    assert "samples_target" in payload["error_message"]


def test_s1_image_runtime_face_detail_fails_on_incomplete_resume_state(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    _create_required_flux_assets(module, _base_job_input())
    client = TestClient(module.app)

    submit = client.post(
        "/jobs",
        json={
            "input": _base_job_input(
                mode="face_detail",
                resume_checkpoint={
                    "workflow_id": "base-image-ipadapter-impact",
                    "workflow_version": "2026-03-31",
                    "base_model_id": "flux-schnell-v1",
                    "seed": 42,
                    "stage": "base_render",
                    "provider": "modal",
                    "provider_job_id": "prompt-1",
                    "successful_node_ids": ["save_base_image"],
                    "intermediate_artifacts": [],
                    "metadata_json": {"face_detection_confidence": 0.61},
                },
            )
        },
    )
    result = client.get(submit.json()["result_url"])

    assert result.json()["error_code"] == "RESUME_STATE_INCOMPLETE"


def test_modal_runtime_provider_can_consume_s1_image_runtime_locally(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    monkeypatch.setattr(module, "_submit_prompt", lambda *_args, **_kwargs: "prompt-1")
    monkeypatch.setattr(
        module,
        "_poll_history",
        lambda _prompt_id: {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
                },
                "face_detector": {"metrics": {"bbox_confidence": 0.84}},
            }
        },
    )
    _create_required_flux_assets(module, _base_job_input())
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(tiny_png_bytes())
    client = TestClient(module.app)

    def fake_post(url: str, payload: dict, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        response = client.post(urlparse(url).path, json=payload)
        assert response.status_code == 200, response.text
        return response.json()

    def fake_get(url: str, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
        response = client.get(urlparse(url).path)
        assert response.status_code == 200, response.text
        return response.json()

    monkeypatch.setattr("vixenbliss_creator.runtime_providers.adapters._json_post", fake_post)
    monkeypatch.setattr("vixenbliss_creator.runtime_providers.adapters._json_get", fake_get)

    from vixenbliss_creator.runtime_providers import ModalRuntimeProviderClient, RuntimeProviderSettings, ServiceRuntime

    settings = RuntimeProviderSettings(modal_endpoint_s1_image="http://testserver", provider_poll_interval_seconds=0)
    runtime_client = ModalRuntimeProviderClient(settings)

    handle = runtime_client.submit_job(ServiceRuntime.S1_IMAGE, _base_job_input())
    result = runtime_client.fetch_result(handle)

    assert result["provider"] == "modal"
    assert result["runtime_stage"] == "identity_image"
    assert result["artifacts"][0]["role"] == "base_image"


def test_s1_image_runtime_websocket_streams_recorded_progress_events(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    monkeypatch.setattr(module, "_ensure_comfyui_running", lambda **_kwargs: None)
    monkeypatch.setattr(module, "_download_remote_file", lambda *_args, **_kwargs: "reference.png")
    monkeypatch.setattr(module, "_submit_prompt", lambda *_args, **_kwargs: "prompt-1")
    monkeypatch.setattr(
        module,
        "_poll_history",
        lambda _prompt_id: {
            "outputs": {
                "save_base_image": {
                    "images": [{"filename": "base.png", "subfolder": "vb", "type": "output"}],
                },
                "face_detector": {"metrics": {"bbox_confidence": 0.84}},
            }
        },
    )
    _create_required_flux_assets(module, _base_job_input())
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb").mkdir(parents=True, exist_ok=True)
    (Path(module.COMFYUI_OUTPUT_DIR) / "vb" / "base.png").write_bytes(tiny_png_bytes())
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input()})
    job_id = submit.json()["job_id"]

    with client.websocket_connect(f"/ws/jobs/{job_id}") as websocket:
        events = []
        while True:
            try:
                events.append(websocket.receive_json())
            except Exception:
                break

    stages = [event["stage"] for event in events]
    assert "accepted" in stages
    assert "submitting_prompt" in stages
    assert "base_render_complete" in stages
    assert stages[-1] == "completed"


def test_s1_image_runtime_can_delegate_execution_to_modal_worker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("S1_IMAGE_EXECUTION_BACKEND", "modal")
    module = _load_runtime_module(tmp_path, monkeypatch)

    class FakeRemoteFunction:
        def remote(self, payload: dict) -> dict:
            assert payload["runtime_stage"] == "identity_image"
            return {
                "provider": "modal",
                "runtime_stage": "identity_image",
                "artifacts": [{"role": "base_image", "uri": "modal://base.png", "content_type": "image/png", "metadata_json": {}}],
                "metadata": {
                    "modal_progress_events": [
                        {"stage": "building_workflow", "message": "Preparing workflow", "progress": 0.42},
                        {"stage": "base_render_complete", "message": "Base render finished", "progress": 0.94},
                    ]
                },
            }

    monkeypatch.setattr(modal.Function, "from_name", lambda *_args, **_kwargs: FakeRemoteFunction())
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input()})

    assert submit.status_code == 200
    assert submit.json()["output"]["artifacts"][0]["uri"] == "modal://base.png"
    stages = [event["stage"] for event in submit.json()["metadata"]["progress_events"]]
    assert "dispatching_modal_job" in stages
    assert "building_workflow" in stages
    assert "modal_job_completed" in stages


def test_s1_image_runtime_marks_modal_error_results_as_failed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("S1_IMAGE_EXECUTION_BACKEND", "modal")
    module = _load_runtime_module(tmp_path, monkeypatch)

    class FakeRemoteFunction:
        def remote(self, payload: dict) -> dict:
            assert payload["runtime_stage"] == "identity_image"
            return {
                "provider": "modal",
                "runtime_stage": "identity_image",
                "artifacts": [],
                "error_code": "REFERENCE_IMAGE_NOT_FOUND",
                "error_message": "reference_face_image_url could not be resolved",
                "metadata": {
                    "modal_progress_events": [
                        {"stage": "building_workflow", "message": "Preparing workflow", "progress": 0.42},
                    ]
                },
            }

    monkeypatch.setattr(modal.Function, "from_name", lambda *_args, **_kwargs: FakeRemoteFunction())
    client = TestClient(module.app)

    submit = client.post("/jobs", json={"input": _base_job_input()})

    assert submit.status_code == 200
    assert submit.json()["status"] == "failed"
    stages = [event["stage"] for event in submit.json()["metadata"]["progress_events"]]
    assert "dispatching_modal_job" in stages
    assert "building_workflow" in stages
    assert "modal_job_completed" in stages
    assert stages[-1] == "failed"
    assert submit.json()["output"]["error_code"] == "REFERENCE_IMAGE_NOT_FOUND"


def test_s1_image_runtime_healthcheck_can_delegate_to_modal_worker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("S1_IMAGE_EXECUTION_BACKEND", "modal")
    module = _load_runtime_module(tmp_path, monkeypatch)

    class FakeHealthcheckFunction:
        def remote(self, *, deep: bool) -> dict:
            assert deep is True
            return {
                "ok": True,
                "provider_ready": True,
                "service": "s1_image",
                "provider": "modal",
                "progress_transport": "websocket_optional",
                "runtime_checks": {"workflow_baked": True},
                "runtime_contract": {"runtime_stage": "identity_image"},
                "comfyui_reachable": True,
            }

    monkeypatch.setattr(modal.Function, "from_name", lambda *_args, **_kwargs: FakeHealthcheckFunction())
    client = TestClient(module.app)

    response = client.get("/healthcheck?deep=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["orchestrator_host"] == "coolify"
    assert payload["startup_mode"] == "remote_gpu_worker"


def test_s1_image_runtime_lab_handoff_allows_missing_reference_face_url(tmp_path: Path, monkeypatch) -> None:
    module = _load_runtime_module(tmp_path, monkeypatch)
    client = TestClient(module.app)
    _authenticate_test_client(module, client)
    captured: dict[str, object] = {}

    def fake_submit_job(payload: dict) -> dict:
        captured["payload"] = payload
        return {
            "job_id": "job-no-ref",
            "status": "completed",
            "result_url": "/jobs/job-no-ref/result",
            "progress_url": "/ws/jobs/job-no-ref",
            "metadata": {"progress_events": []},
        }

    monkeypatch.setattr(module, "submit_job", fake_submit_job)

    ready_payload = _ready_lab_session(client, "session-4")
    assert ready_payload["can_handoff"] is True

    response = client.post("/lab/s1-image", json={"session_id": "session-4"})

    assert response.status_code == 200
    assert captured["payload"]["input"]["reference_face_image_url"] is None
    assert captured["payload"]["input"]["ip_adapter"]["enabled"] is False
    assert response.json()["panel"]["reference_face"]["source"] == "none"
