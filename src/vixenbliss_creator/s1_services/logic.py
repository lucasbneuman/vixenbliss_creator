from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import PurePosixPath

from .models import (
    DatasetServiceInput,
    DatasetShot,
    GenerationManifest,
    GenerationServiceInput,
    LoraTrainingServiceInput,
    SeedBundle,
)


DEFAULT_REALISM_PROFILE = "photorealistic_adult_reference_v1"
DEFAULT_SOURCE_STRATEGY = "avatar_prompt_plus_shot_plan_v1"
DEFAULT_SAMPLES_TARGET = 40
DATASET_REALISM_BLOCK = (
    "adult real person, photorealistic editorial camera capture, natural skin texture, lifelike pores, "
    "realistic anatomy, believable body proportions, subtle imperfections, cinematic but realistic lighting, "
    "high detail photography, DSLR lens rendering, no synthetic or illustrated look"
)
DATASET_NEGATIVE_TERMS = (
    "low quality, anatomy drift, identity drift, extra limbs, cgi, 3d, illustration, anime, plastic skin, mannequin, "
    "duplicate body, bad anatomy, watermark, text, body horror, minors"
)
ANGLE_DESCRIPTIONS = {
    "front": "front-facing view",
    "left_three_quarter": "left three-quarter view",
    "right_three_quarter": "right three-quarter view",
    "left_profile": "left profile view",
    "right_profile": "right profile view",
}
FRAMING_DESCRIPTIONS = {
    "close_up_face": "close-up face portrait",
    "medium": "medium shot from torso to head",
    "full_body": "full body standing shot",
}
WARDROBE_DESCRIPTIONS = {
    "clothed": "styled editorial outfit",
    "nude": "tasteful nude adult reference styling",
}
SHOT_TEMPLATE_SEQUENCE = (
    ("close_up_face", "head_turn_portrait", "calm confident expression"),
    ("medium", "editorial_standing", "subtle direct gaze"),
    ("full_body", "balanced_stance", "confident relaxed expression"),
    ("full_body", "contrapposto_stance", "soft neutral expression"),
)
WARDROBE_SEQUENCE = (
    ("clothed", "SFW"),
    ("nude", "NSFW"),
)
ANGLE_SEQUENCE = (
    "front",
    "left_three_quarter",
    "right_three_quarter",
    "left_profile",
    "right_profile",
)


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


def _stringify_context_value(value: object) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _english_identity_summary(identity_context: dict[str, object]) -> str:
    fallback_name = (
        _stringify_context_value(identity_context.get("identity_summary"))
        or _stringify_context_value(identity_context.get("summary"))
    )
    display_name = _stringify_context_value(identity_context.get("display_name")) or fallback_name or "This identity"
    archetype = _stringify_context_value(identity_context.get("archetype")) or "editorial persona"
    vertical = _stringify_context_value(identity_context.get("vertical")) or "premium"
    style = _stringify_context_value(identity_context.get("style")) or "editorial"
    return (
        f"{display_name}, a {style} synthetic identity designed for the {vertical} vertical "
        f"with a {archetype} archetype"
    )


def _english_persona_summary(identity_context: dict[str, object]) -> str:
    fallback_name = (
        _stringify_context_value(identity_context.get("identity_summary"))
        or _stringify_context_value(identity_context.get("summary"))
    )
    display_name = _stringify_context_value(identity_context.get("display_name")) or fallback_name or "This identity"
    archetype = _stringify_context_value(identity_context.get("archetype")) or "editorial persona"
    voice_tone = _stringify_context_value(identity_context.get("voice_tone")) or "controlled"
    return (
        f"{display_name} maintains a {voice_tone} delivery with a {archetype} persona "
        "optimized for consistent content generation."
    )


def _english_tagline(identity_context: dict[str, object]) -> str:
    style = _stringify_context_value(identity_context.get("style")) or "premium"
    vertical = _stringify_context_value(identity_context.get("vertical")) or "content"
    return f"Synthetic {style} identity prepared for repeatable {vertical} content production."


def _build_prompt_details(identity_context: dict[str, object]) -> str:
    details: list[str] = []
    display_name = _stringify_context_value(identity_context.get("display_name"))
    if display_name:
        details.append(f"Character: {display_name}.")

    archetype = _stringify_context_value(identity_context.get("archetype"))
    if archetype:
        details.append(f"Archetype: {archetype}.")

    vertical = _stringify_context_value(identity_context.get("vertical"))
    style = _stringify_context_value(identity_context.get("style"))
    if vertical or style:
        profile_bits = [part for part in (vertical, style) if part]
        details.append(f"Commercial profile: {' / '.join(profile_bits)}.")

    voice_tone = _stringify_context_value(identity_context.get("voice_tone"))
    if voice_tone:
        details.append(f"Voice tone: {voice_tone}.")

    occupation = _stringify_context_value(identity_context.get("occupation_or_content_basis"))
    if occupation:
        details.append(f"Content basis: {occupation}.")

    details.append(f"Persona summary: {_english_persona_summary(identity_context)}.")
    details.append(f"Identity summary: {_english_tagline(identity_context)}.")

    personality_axes = identity_context.get("personality_axes")
    if isinstance(personality_axes, dict) and personality_axes:
        axis_summary = ", ".join(f"{axis}={value}" for axis, value in sorted(personality_axes.items()))
        details.append(f"Personality axes: {axis_summary}.")

    visual_profile = identity_context.get("visual_profile")
    if isinstance(visual_profile, dict):
        hair_color = _stringify_context_value(visual_profile.get("hair_color"))
        hair_style = _stringify_context_value(visual_profile.get("hair_style"))
        visual_archetype = _stringify_context_value(visual_profile.get("archetype"))
        visual_bits = [part for part in (hair_color, hair_style, visual_archetype) if part]
        if visual_bits:
            details.append(f"Visual cues: {', '.join(visual_bits)}.")

    interests = identity_context.get("interests")
    if isinstance(interests, list):
        interest_bits = [_stringify_context_value(item) for item in interests]
        interest_bits = [item for item in interest_bits if item]
        if interest_bits:
            details.append(f"Interests: {', '.join(interest_bits[:4])}.")

    return " ".join(details)


def _join_prompt_parts(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def _bounded_text(value: str, *, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip(" ,.;") + "..."


def _flatten_hint_values(hints: dict[str, object]) -> list[str]:
    values: list[str] = []
    for raw_value in hints.values():
        if isinstance(raw_value, str):
            stripped = raw_value.strip()
            if stripped:
                values.append(stripped)
        elif isinstance(raw_value, list):
            for item in raw_value:
                if isinstance(item, str):
                    stripped = item.strip()
                    if stripped:
                        values.append(stripped)
    return values


def _build_generation_prompt(
    *,
    identity_summary: str,
    tone: object,
    prompt_details: str,
    copilot_prompt_template: str | None,
    prompt_hints: dict[str, object],
) -> str:
    workflow_strategy = (copilot_prompt_template or "").strip()
    prompt_hint_block = "; ".join(_flatten_hint_values(prompt_hints))
    base_prompt = (
        f"Create a consistent identity dataset portrait for {identity_summary}. "
        f"Preserve premium visual coherence, natural anatomy, face consistency and reusable LoRA training coverage. "
        f"Tone: {tone}. "
        f"{prompt_details}"
    )
    if workflow_strategy:
        base_prompt = _join_prompt_parts(base_prompt, f"Workflow guidance: {workflow_strategy}.")
    if prompt_hint_block:
        base_prompt = _join_prompt_parts(base_prompt, f"Additional prompt hints: {prompt_hint_block}.")
    return _bounded_text(base_prompt, limit=1200)


def _merge_negative_prompt(base_negative_prompt: str) -> str:
    merged: list[str] = []
    seen: set[str] = set()
    for raw_chunk in (base_negative_prompt, DATASET_NEGATIVE_TERMS):
        for term in raw_chunk.split(","):
            cleaned = term.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(cleaned)
    return ", ".join(merged)


def _canonical_shot_specs() -> list[tuple[str, str, str, str, str]]:
    specs: list[tuple[str, str, str, str, str]] = []
    for framing, pose_family, expression in SHOT_TEMPLATE_SEQUENCE:
        for camera_angle in ANGLE_SEQUENCE:
            for wardrobe_state, class_name in WARDROBE_SEQUENCE:
                specs.append((framing, pose_family, expression, camera_angle, class_name if wardrobe_state == "clothed" else "NSFW"))
    return specs


def _select_shot_specs(samples_target: int) -> list[tuple[str, str, str, str, str]]:
    if samples_target < 4:
        raise ValueError("samples_target must be at least 4 to build a dataset shot plan")
    if samples_target % 2 != 0:
        raise ValueError("samples_target must be even to satisfy the 50/50 dataset balance policy")
    canonical = _canonical_shot_specs()
    if samples_target > len(canonical):
        raise ValueError("samples_target must be lower than or equal to 40 for the current shot planner")
    return canonical[:samples_target]


def _build_variant_prompt(
    *,
    avatar_identity_block: str,
    framing: str,
    pose_family: str,
    expression: str,
    camera_angle: str,
    wardrobe_state: str,
) -> str:
    variant_block = (
        f"{FRAMING_DESCRIPTIONS[framing]}, {ANGLE_DESCRIPTIONS[camera_angle]}, "
        f"{WARDROBE_DESCRIPTIONS[wardrobe_state]}, {pose_family.replace('_', ' ')}, {expression}."
    )
    return _join_prompt_parts(avatar_identity_block, DATASET_REALISM_BLOCK, variant_block)


def _build_caption(*, framing: str, camera_angle: str, wardrobe_state: str, pose_family: str) -> str:
    return (
        f"adult real person, {framing.replace('_', ' ')}, {camera_angle.replace('_', ' ')}, "
        f"{wardrobe_state}, {pose_family.replace('_', ' ')}, photorealistic reference photo"
    )


def build_dataset_shot_plan(
    *,
    dataset_version: str,
    avatar_identity_block: str,
    base_negative_prompt: str,
    seed_bundle: SeedBundle,
    samples_target: int = DEFAULT_SAMPLES_TARGET,
    realism_profile: str = DEFAULT_REALISM_PROFILE,
    source_strategy: str = DEFAULT_SOURCE_STRATEGY,
) -> list[DatasetShot]:
    if isinstance(seed_bundle, dict):
        seed_bundle = SeedBundle.model_validate(seed_bundle)
    shots: list[DatasetShot] = []
    merged_negative_prompt = _merge_negative_prompt(base_negative_prompt)
    for shot_index, (framing, pose_family, expression, camera_angle, class_name) in enumerate(
        _select_shot_specs(samples_target),
        start=1,
    ):
        wardrobe_state = "clothed" if class_name == "SFW" else "nude"
        shots.append(
            DatasetShot(
                shot_index=shot_index,
                sample_id=f"{dataset_version}-{shot_index:03d}",
                class_name=class_name,
                wardrobe_state=wardrobe_state,
                framing=framing,
                shot_type=framing,
                camera_angle=camera_angle,
                pose_family=pose_family,
                expression=expression,
                prompt=_build_variant_prompt(
                    avatar_identity_block=avatar_identity_block,
                    framing=framing,
                    pose_family=pose_family,
                    expression=expression,
                    camera_angle=camera_angle,
                    wardrobe_state=wardrobe_state,
                ),
                negative_prompt=merged_negative_prompt,
                caption=_build_caption(
                    framing=framing,
                    camera_angle=camera_angle,
                    wardrobe_state=wardrobe_state,
                    pose_family=pose_family,
                ),
                seed=_dataset_sample_seed(seed_bundle.dataset_seed, index=shot_index),
                realism_profile=realism_profile,
                source_strategy=source_strategy,
            )
        )
    return shots


def _build_dataset_files(
    *,
    identity_id: str,
    character_id: str,
    dataset_version: str,
    shot_plan: list[DatasetShot],
) -> tuple[list[dict], dict]:
    if not shot_plan:
        raise ValueError("dataset shot plan must contain at least one sample")

    composition_counts = Counter(shot.class_name for shot in shot_plan)
    files: list[dict] = []
    for shot in shot_plan:
        files.append(
            {
                "sample_id": shot.sample_id,
                "identity_id": identity_id,
                "character_id": character_id,
                "class_name": shot.class_name,
                "path": f"images/{shot.class_name}/{shot.camera_angle}/sample-{shot.shot_index:03d}.png",
                "origin": "generated_dataset_shot",
                "variation_group": shot.framing,
                "framing": shot.framing,
                "shot_type": shot.shot_type,
                "camera_angle": shot.camera_angle,
                "pose": shot.pose_family,
                "pose_family": shot.pose_family,
                "expression": shot.expression,
                "wardrobe_state": shot.wardrobe_state,
                "prompt": shot.prompt,
                "negative_prompt": shot.negative_prompt,
                "caption": shot.caption,
                "seed": shot.seed,
                "realism_profile": shot.realism_profile,
                "source_strategy": shot.source_strategy,
            }
        )
    composition = {
        "policy": "balanced_50_50",
        "SFW": composition_counts.get("SFW", 0),
        "NSFW": composition_counts.get("NSFW", 0),
    }
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
            "samples_target": payload.samples_target,
            "realism_profile": payload.realism_profile,
            "source_strategy": payload.source_strategy,
        }
    )
    identity_summary = _english_identity_summary(payload.identity_context)
    tone = payload.identity_context.get("voice_tone") or payload.identity_context.get("style") or "editorial"
    prompt_details = _build_prompt_details(payload.identity_context)
    prompt = _build_generation_prompt(
        identity_summary=identity_summary,
        tone=tone,
        prompt_details=prompt_details,
        copilot_prompt_template=payload.copilot_prompt_template,
        prompt_hints=payload.prompt_hints,
    )
    negative_prompt = _bounded_text(
        _merge_negative_prompt(
        ", ".join(
            [
                chunk
                for chunk in [
                    payload.copilot_negative_prompt or "",
                    ", ".join(_flatten_hint_values(payload.negative_prompt_hints)),
                    DATASET_NEGATIVE_TERMS,
                ]
                if chunk
            ]
        )
        ),
        limit=1200,
    )
    artifact_path = str(PurePosixPath("artifacts") / "s1-llm" / str(payload.identity_id) / f"generation-manifest-{digest[:12]}.json")
    seed_bundle = SeedBundle(
        portrait_seed=_seed_from_digest(digest, 0),
        variation_seed=_seed_from_digest(digest, 1),
        dataset_seed=_seed_from_digest(digest, 2),
    )
    dataset_version = _dataset_version_from_digest(digest)
    return GenerationManifest(
        identity_id=payload.identity_id,
        prompt=prompt,
        negative_prompt=negative_prompt,
        seed_bundle=seed_bundle,
        samples_target=payload.samples_target,
        workflow_id=payload.workflow_id,
        workflow_version=payload.workflow_version,
        workflow_family=payload.workflow_family,
        workflow_registry_source=payload.workflow_registry_source,
        base_model_id=payload.base_model_id,
        realism_profile=payload.realism_profile,
        source_strategy=payload.source_strategy,
        dataset_shot_plan=build_dataset_shot_plan(
            dataset_version=dataset_version,
            avatar_identity_block=prompt,
            base_negative_prompt=negative_prompt,
            seed_bundle=seed_bundle,
            samples_target=payload.samples_target,
            realism_profile=payload.realism_profile,
            source_strategy=payload.source_strategy,
        ),
        comfy_parameters={
            "width": payload.image_width,
            "height": payload.image_height,
            "reference_face_image_url": payload.reference_face_image_url,
            "ip_adapter": payload.ip_adapter,
            "workflow_family": payload.workflow_family,
            "workflow_registry_source": payload.workflow_registry_source,
            "copilot_prompt_template": payload.copilot_prompt_template,
            "copilot_negative_prompt": payload.copilot_negative_prompt,
            "prompt_hints": payload.prompt_hints,
            "negative_prompt_hints": payload.negative_prompt_hints,
        },
        artifact_path=artifact_path,
    )


def build_dataset_result(payload: DatasetServiceInput) -> dict:
    if payload.face_detection_confidence is None:
        raise ValueError("face_detection_confidence is required to validate dataset generation")
    character_id = str(payload.metadata_json.get("character_id") or payload.identity_id)
    shot_plan = payload.dataset_shot_plan or payload.generation_manifest.dataset_shot_plan
    if not shot_plan:
        raise ValueError("dataset_shot_plan is required to materialize the LoRA dataset manifest")
    seed_bundle = payload.generation_manifest.seed_bundle.model_dump(mode="json")
    digest = _stable_digest(
        {
            "identity_id": str(payload.identity_id),
            "manifest": payload.generation_manifest.model_dump(mode="json"),
            "samples_target": payload.samples_target,
            "metadata_json": payload.metadata_json,
        }
    )
    dataset_version = shot_plan[0].sample_id.rsplit("-", 1)[0]
    identity_root = PurePosixPath(payload.artifact_root) / str(payload.identity_id) / "datasets" / dataset_version
    manifest_path = str(identity_root / "dataset-manifest.json")
    package_path = str(identity_root / "dataset-package.zip")
    base_image_path = str(identity_root / "base-image.png")
    files, composition = _build_dataset_files(
        identity_id=str(payload.identity_id),
        character_id=character_id,
        dataset_version=dataset_version,
        shot_plan=shot_plan,
    )
    checksum = _stable_digest({"dataset_package_path": package_path, "digest": digest})
    workflow_extensions = ["ComfyUI-BatchingNodes", "ComfyPack"]
    return {
        "provider": "modal",
        "service": "s1_image",
        "model_family": "flux",
        "workflow_id": payload.generation_manifest.workflow_id,
        "workflow_version": payload.generation_manifest.workflow_version,
        "workflow_family": payload.generation_manifest.workflow_family,
        "workflow_registry_source": payload.generation_manifest.workflow_registry_source,
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
                    "realism_profile": payload.generation_manifest.realism_profile,
                    "source_strategy": payload.generation_manifest.source_strategy,
                    "workflow_family": payload.generation_manifest.workflow_family,
                    "workflow_registry_source": payload.generation_manifest.workflow_registry_source,
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
                    "workflow_extensions": workflow_extensions,
                    "realism_profile": payload.generation_manifest.realism_profile,
                    "source_strategy": payload.generation_manifest.source_strategy,
                    "workflow_family": payload.generation_manifest.workflow_family,
                    "workflow_registry_source": payload.generation_manifest.workflow_registry_source,
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
                    "workflow_extensions": workflow_extensions,
                    "realism_profile": payload.generation_manifest.realism_profile,
                    "source_strategy": payload.generation_manifest.source_strategy,
                    "workflow_family": payload.generation_manifest.workflow_family,
                    "workflow_registry_source": payload.generation_manifest.workflow_registry_source,
                },
            },
        ],
        "dataset_manifest": {
            "schema_version": "1.1.0",
            "identity_id": str(payload.identity_id),
            "character_id": character_id,
            "dataset_version": dataset_version,
            "artifact_path": manifest_path,
            "dataset_package_path": package_path,
            "sample_count": payload.samples_target,
            "generated_samples": payload.samples_target,
            "composition": composition,
            "files": files,
            "workflow_extensions": workflow_extensions,
            "workflow_id": payload.generation_manifest.workflow_id,
            "workflow_version": payload.generation_manifest.workflow_version,
            "workflow_family": payload.generation_manifest.workflow_family,
            "workflow_registry_source": payload.generation_manifest.workflow_registry_source,
            "base_model_id": payload.generation_manifest.base_model_id,
            "prompt": payload.generation_manifest.prompt,
            "negative_prompt": payload.generation_manifest.negative_prompt,
            "seed_bundle": seed_bundle,
            "reference_face_image_url": payload.reference_face_image_url,
            "face_detection_confidence": payload.face_detection_confidence,
            "review_required": True,
            "checksum_sha256": checksum,
            "storage_path": identity_root.as_posix(),
            "realism_profile": payload.generation_manifest.realism_profile,
            "source_strategy": payload.generation_manifest.source_strategy,
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
                "compatibility_notes": "Flux.1 Schnell compliant",
            },
        },
    }
