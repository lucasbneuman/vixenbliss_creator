from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
from uuid import uuid4

from .models import DatasetServiceInput, GenerationManifest, GenerationServiceInput, LoraTrainingServiceInput, SeedBundle


def _stable_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _seed_from_digest(digest: str, offset: int) -> int:
    start = offset * 8
    return int(digest[start : start + 8], 16) % (2**31 - 1)


def _dataset_version_from_digest(digest: str) -> str:
    return f"dataset-{digest[:12]}"


def _dataset_sample_seed(dataset_seed: int, *, index: int) -> int:
    return (dataset_seed + (index * 104_729)) % (2**31 - 1)


def _build_dataset_files(
    *,
    identity_id: str,
    character_id: str,
    dataset_version: str,
    sample_count: int,
    dataset_seed: int,
) -> tuple[list[dict], dict]:
    if sample_count < 4:
        raise ValueError("samples_target must be at least 4 to build a balanced dataset")
    if sample_count % 2 != 0:
        raise ValueError("samples_target must be even to satisfy the 50/50 dataset balance policy")

    half = sample_count // 2
    composition = {
        "policy": "balanced_50_50",
        "with_clothes": half,
        "without_clothes": half,
    }
    files: list[dict] = []
    sample_index = 0
    framing_cycle = ("close_up", "medium", "full_body")
    pose_cycle = ("front", "three_quarter", "profile")
    for class_name, count in (("with_clothes", half), ("without_clothes", half)):
        for class_offset in range(count):
            sample_index += 1
            variation_group = framing_cycle[(sample_index - 1) % len(framing_cycle)]
            files.append(
                {
                    "sample_id": f"{dataset_version}-{sample_index:03d}",
                    "identity_id": identity_id,
                    "character_id": character_id,
                    "class_name": class_name,
                    "path": f"images/{class_name}/sample-{class_offset + 1:03d}.png",
                    "origin": "generated_base_image",
                    "variation_group": variation_group,
                    "framing": variation_group,
                    "pose": pose_cycle[(sample_index - 1) % len(pose_cycle)],
                    "seed": _dataset_sample_seed(dataset_seed, index=sample_index),
                }
            )
    return files, composition


def build_generation_manifest(payload: GenerationServiceInput) -> GenerationManifest:
    digest = _stable_digest(
        {
            "identity_id": str(payload.identity_id),
            "identity_context": payload.identity_context,
            "workflow_id": payload.workflow_id,
            "workflow_version": payload.workflow_version,
            "base_model_id": payload.base_model_id,
            "seed_basis": payload.seed_basis or str(payload.identity_id),
        }
    )
    identity_summary = payload.identity_context.get("identity_summary") or payload.identity_context.get("summary") or "synthetic premium identity"
    tone = payload.identity_context.get("voice_tone") or payload.identity_context.get("style") or "editorial"
    prompt = (
        f"Create a consistent identity dataset portrait for {identity_summary}. "
        f"Preserve premium visual coherence, natural anatomy, face consistency and reusable training coverage. "
        f"Tone: {tone}."
    )
    negative_prompt = "low quality, anatomy drift, extra limbs, minors, watermark, text, body horror"
    artifact_path = str(PurePosixPath("artifacts") / "s1-llm" / str(payload.identity_id) / f"generation-manifest-{digest[:12]}.json")
    return GenerationManifest(
        identity_id=payload.identity_id,
        prompt=prompt,
        negative_prompt=negative_prompt,
        seed_bundle=SeedBundle(
            portrait_seed=_seed_from_digest(digest, 0),
            variation_seed=_seed_from_digest(digest, 1),
            dataset_seed=_seed_from_digest(digest, 2),
        ),
        workflow_id=payload.workflow_id,
        workflow_version=payload.workflow_version,
        base_model_id=payload.base_model_id,
        comfy_parameters={
            "width": payload.image_width,
            "height": payload.image_height,
            "reference_face_image_url": payload.reference_face_image_url,
            "ip_adapter": payload.ip_adapter,
            "prompt_hints": payload.prompt_hints,
            "negative_prompt_hints": payload.negative_prompt_hints,
        },
        artifact_path=artifact_path,
    )


def build_dataset_result(payload: DatasetServiceInput) -> dict:
    if payload.face_detection_confidence is None:
        raise ValueError("face_detection_confidence is required to validate dataset generation")
    character_id = str(payload.metadata_json.get("character_id") or payload.identity_id)
    seed_bundle = payload.generation_manifest.seed_bundle.model_dump(mode="json")
    digest = _stable_digest(
        {
            "identity_id": str(payload.identity_id),
            "manifest": payload.generation_manifest.model_dump(mode="json"),
            "samples_target": payload.samples_target,
            "metadata_json": payload.metadata_json,
        }
    )
    dataset_version = _dataset_version_from_digest(digest)
    identity_root = PurePosixPath(payload.artifact_root) / str(payload.identity_id) / dataset_version
    manifest_path = str(identity_root / "dataset-manifest.json")
    package_path = str(identity_root / "dataset-package.zip")
    base_image_path = str(identity_root / "base-image.png")
    files, composition = _build_dataset_files(
        identity_id=str(payload.identity_id),
        character_id=character_id,
        dataset_version=dataset_version,
        sample_count=payload.samples_target,
        dataset_seed=payload.generation_manifest.seed_bundle.dataset_seed,
    )
    checksum = _stable_digest({"dataset_package_path": package_path, "digest": digest})
    return {
        "provider": "modal",
        "service": "s1_image",
        "model_family": "flux",
        "workflow_id": payload.generation_manifest.workflow_id,
        "workflow_version": payload.generation_manifest.workflow_version,
        "base_model_id": payload.generation_manifest.base_model_id,
        "artifacts": [
            {
                "artifact_type": "base_image",
                "storage_path": base_image_path,
                "content_type": "image/png",
                "metadata_json": {
                    "identity_id": str(payload.identity_id),
                    "character_id": character_id,
                    "seed": payload.generation_manifest.seed_bundle.portrait_seed,
                    "seed_bundle": seed_bundle,
                    "face_detection_confidence": payload.face_detection_confidence,
                },
            },
            {
                "artifact_type": "dataset_manifest",
                "storage_path": manifest_path,
                "content_type": "application/json",
                "metadata_json": {
                    "identity_id": str(payload.identity_id),
                    "character_id": character_id,
                    "seed_bundle": seed_bundle,
                    "samples_target": payload.samples_target,
                    "reference_face_image_url": payload.reference_face_image_url,
                    "source_manifest_path": payload.generation_manifest.artifact_path,
                },
            },
            {
                "artifact_type": "dataset_package",
                "storage_path": package_path,
                "content_type": "application/zip",
                "checksum_sha256": checksum,
                "metadata_json": {
                    "identity_id": str(payload.identity_id),
                    "character_id": character_id,
                    "seed_bundle": seed_bundle,
                    "samples_target": payload.samples_target,
                    "seed": payload.generation_manifest.seed_bundle.dataset_seed,
                },
            },
        ],
        "dataset_manifest": {
            "schema_version": "1.0.0",
            "identity_id": str(payload.identity_id),
            "character_id": character_id,
            "dataset_version": dataset_version,
            "artifact_path": manifest_path,
            "dataset_package_path": package_path,
            "sample_count": payload.samples_target,
            "generated_samples": payload.samples_target,
            "composition": composition,
            "files": files,
            "workflow_id": payload.generation_manifest.workflow_id,
            "workflow_version": payload.generation_manifest.workflow_version,
            "base_model_id": payload.generation_manifest.base_model_id,
            "prompt": payload.generation_manifest.prompt,
            "negative_prompt": payload.generation_manifest.negative_prompt,
            "seed_bundle": seed_bundle,
            "reference_face_image_url": payload.reference_face_image_url,
            "face_detection_confidence": payload.face_detection_confidence,
            "review_required": True,
            "checksum_sha256": checksum,
        },
    }


def build_lora_training_result(payload: LoraTrainingServiceInput) -> dict:
    if payload.model_family != "flux":
        raise ValueError("lora training only supports the flux model family")
    dataset_locator = payload.dataset_package_path or json.dumps(payload.dataset_manifest, sort_keys=True)
    handoff_mode = "dataset_package_path" if payload.dataset_package_path else "dataset_manifest"
    digest = _stable_digest(
        {
            "identity_id": str(payload.identity_id),
            "dataset_locator": dataset_locator,
            "base_model_id": payload.base_model_id,
            "training_config": payload.training_config,
        }
    )
    identity_root = PurePosixPath(payload.artifact_root) / str(payload.identity_id)
    lora_path = str(identity_root / f"lora-model-{digest[:12]}.safetensors")
    manifest_path = str(identity_root / f"training-result-{digest[:12]}.json")
    checksum = _stable_digest({"lora_path": lora_path, "digest": digest})
    trigger_word = payload.training_config.get("trigger_word") or f"vb_{str(payload.identity_id).replace('-', '')[:8]}"
    steps = int(payload.training_config.get("training_steps", 1200))
    return {
        "provider": "modal",
        "service": "s1_lora_train",
        "base_model_id": payload.base_model_id,
        "model_family": payload.model_family,
        "artifacts": [
            {
                "artifact_type": "lora_model",
                "storage_path": lora_path,
                "content_type": "application/octet-stream",
                "checksum_sha256": checksum,
                "metadata_json": {
                    "training_steps": steps,
                    "trigger_word": trigger_word,
                    "result_manifest_path": manifest_path,
                },
            }
        ],
        "training_manifest": {
            "identity_id": str(payload.identity_id),
            "base_model_id": payload.base_model_id,
            "dataset_package_path": payload.dataset_package_path,
            "dataset_manifest": payload.dataset_manifest,
            "dataset_source": {
                "handoff_mode": handoff_mode,
                "dataset_locator": dataset_locator,
            },
            "training_steps": steps,
            "trigger_word": trigger_word,
            "result_manifest_path": manifest_path,
            "lora_model_path": lora_path,
            "checksum_sha256": checksum,
            "model_registry": {
                "version_name": f"lora-{digest[:8]}",
                "display_name": f"S1 LoRA {str(payload.identity_id)[:8]}",
                "base_model_id": payload.base_model_id,
                "storage_path": lora_path,
                "provider": "modal",
            },
        },
    }
