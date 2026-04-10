from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import PurePosixPath

from .models import (
    DEFAULT_RENDER_SAMPLES_TARGET,
    DEFAULT_SELECTION_POLICY,
    DatasetServiceInput,
    DatasetShot,
    GenerationManifest,
    GenerationServiceInput,
    LoraTrainingServiceInput,
    SeedBundle,
)

DEFAULT_REALISM_PROFILE = "photorealistic_adult_reference_v1"
DEFAULT_SOURCE_STRATEGY = "avatar_prompt_plus_shot_plan_v2"
DATASET_REALISM_BLOCK = (
    "adult real person, photorealistic editorial camera capture, natural skin texture, lifelike pores, "
    "realistic anatomy, believable body proportions, subtle imperfections, credible depth cues, cinematic but realistic lighting"
)
QUALITY_GUARD_BLOCK = (
    "full body visibility when requested, intact hands and feet, complete limbs, consistent eyes, "
    "no accidental crop, no duplicate body parts, no stylized rendering"
)
DATASET_NEGATIVE_TERMS = (
    "low quality, anatomy drift, identity drift, extra limbs, cgi, 3d, illustration, anime, plastic skin, mannequin, "
    "duplicate body, bad anatomy, watermark, text, body horror, minors, cropped body, cut off feet, cut off hands, "
    "deformed limbs, asymmetric eyes, over-smoothed skin"
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
ANGLE_RENDER_COUNTS = {
    "front": {("full_body", "clothed"): 6, ("full_body", "nude"): 6, ("medium", "clothed"): 3, ("medium", "nude"): 2, ("close_up_face", "clothed"): 2, ("close_up_face", "nude"): 1},
    "left_three_quarter": {("full_body", "clothed"): 6, ("full_body", "nude"): 6, ("medium", "clothed"): 3, ("medium", "nude"): 2, ("close_up_face", "clothed"): 2, ("close_up_face", "nude"): 1},
    "right_three_quarter": {("full_body", "clothed"): 6, ("full_body", "nude"): 6, ("medium", "clothed"): 2, ("medium", "nude"): 2, ("close_up_face", "clothed"): 2, ("close_up_face", "nude"): 2},
    "left_profile": {("full_body", "clothed"): 3, ("full_body", "nude"): 3, ("medium", "clothed"): 2, ("medium", "nude"): 1, ("close_up_face", "clothed"): 1},
    "right_profile": {("full_body", "clothed"): 3, ("full_body", "nude"): 3, ("medium", "clothed"): 2, ("medium", "nude"): 1, ("close_up_face", "clothed"): 1},
}
TRAINING_COMBO_TARGETS = {
    ("full_body", "clothed"): 12,
    ("full_body", "nude"): 12,
    ("medium", "clothed"): 4,
    ("medium", "nude"): 4,
    ("close_up_face", "clothed"): 4,
    ("close_up_face", "nude"): 4,
}
ANGLE_PRIORITY = {"front": 4, "left_three_quarter": 4, "right_three_quarter": 4, "left_profile": 2, "right_profile": 2}
QUALITY_PRIORITY_WEIGHT = {"hero": 300, "standard": 220, "coverage": 140}
POSE_CATALOG = {
    ("full_body", "clothed"): ["balanced_editorial_stance", "contrapposto_stance", "walking_pose", "hip_shift_pose", "soft_stride_pose", "shoulder_open_pose"],
    ("full_body", "nude"): ["balanced_editorial_stance", "contrapposto_stance", "soft_arch_pose", "weight_shift_pose", "elongated_leg_pose", "subtle_twist_pose"],
    ("medium", "clothed"): ["editorial_standing", "shoulder_turn_pose", "hands_near_waist_pose", "over_the_shoulder_pose"],
    ("medium", "nude"): ["editorial_standing", "soft_torso_turn_pose", "arm_frame_pose", "subtle_profile_pose"],
    ("close_up_face", "clothed"): ["head_turn_portrait", "chin_down_portrait", "direct_gaze_portrait", "soft_profile_portrait"],
    ("close_up_face", "nude"): ["head_turn_portrait", "direct_gaze_portrait", "soft_profile_portrait", "upward_gaze_portrait"],
}
EXPRESSION_CATALOG = {
    "close_up_face": ["calm confident expression", "soft direct gaze", "subtle editorial smirk", "neutral poised expression"],
    "medium": ["subtle direct gaze", "controlled confident expression", "soft neutral expression", "focused editorial expression"],
    "full_body": ["confident relaxed expression", "soft neutral expression", "controlled editorial gaze", "calm poised expression"],
}
LENS_HINTS = {"close_up_face": ["85mm portrait lens", "105mm portrait lens"], "medium": ["50mm editorial lens", "65mm fashion lens"], "full_body": ["35mm fashion lens", "50mm full body lens"]}
LIGHTING_CATALOG = ["soft studio key light with realistic skin falloff", "window light with natural shadow rolloff", "editorial daylight with subtle rim light", "warm diffused softbox lighting with depth"]
BACKGROUND_CATALOG = ["minimal editorial backdrop", "neutral luxury interior backdrop", "soft textured studio wall", "clean lifestyle background with depth separation"]


def _stable_digest(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _seed_from_digest(digest: str, offset: int) -> int:
    return int(digest[offset * 8 : (offset + 1) * 8], 16) % (2**31 - 1)


def _dataset_version_from_digest(digest: str) -> str:
    return f"dataset-{digest[:12]}"


def _dataset_sample_seed(dataset_seed: int, index: int) -> int:
    return (dataset_seed + (index * 104_729)) % (2**31 - 1)


def _flatten_hint_values(hints: dict[str, object]) -> list[str]:
    values: list[str] = []
    for raw in hints.values():
        if isinstance(raw, str) and raw.strip():
            values.append(raw.strip())
        elif isinstance(raw, list):
            values.extend(item.strip() for item in raw if isinstance(item, str) and item.strip())
    return values


def _stringify(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _join_parts(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def _bounded_text(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 3].rstrip(" ,.;") + "..."


def _identity_summary(ctx: dict[str, object]) -> str:
    display_name = _stringify(ctx.get("display_name")) or _stringify(ctx.get("identity_summary")) or _stringify(ctx.get("summary")) or "This identity"
    archetype = _stringify(ctx.get("archetype")) or "editorial persona"
    vertical = _stringify(ctx.get("vertical")) or "premium"
    style = _stringify(ctx.get("style")) or "editorial"
    return f"{display_name}, a {style} synthetic identity designed for the {vertical} vertical with a {archetype} archetype"


def _prompt_details(ctx: dict[str, object]) -> str:
    details: list[str] = []
    for label, key in (("Character", "display_name"), ("Archetype", "archetype"), ("Voice tone", "voice_tone"), ("Content basis", "occupation_or_content_basis")):
        value = _stringify(ctx.get(key))
        if value:
            details.append(f"{label}: {value}.")
    vertical, style = _stringify(ctx.get("vertical")), _stringify(ctx.get("style"))
    if vertical or style:
        details.append(f"Commercial profile: {' / '.join(part for part in (vertical, style) if part)}.")
    identity_name = _stringify(ctx.get("display_name")) or "This identity"
    archetype = _stringify(ctx.get("archetype")) or "editorial persona"
    voice_tone = _stringify(ctx.get("voice_tone")) or "controlled"
    details.append(f"Persona summary: {identity_name} maintains a {voice_tone} delivery with a {archetype} persona optimized for consistent content generation.")
    details.append(f"Identity summary: Synthetic {(style or 'premium')} identity prepared for repeatable {(vertical or 'content')} content production.")
    if isinstance(ctx.get("personality_axes"), dict) and ctx["personality_axes"]:
        details.append("Personality axes: " + ", ".join(f"{axis}={value}" for axis, value in sorted(ctx["personality_axes"].items())) + ".")
    if isinstance(ctx.get("visual_profile"), dict):
        visual_bits = [_stringify(ctx["visual_profile"].get(key)) for key in ("hair_color", "hair_style", "archetype")]
        visual_bits = [bit for bit in visual_bits if bit]
        if visual_bits:
            details.append(f"Visual cues: {', '.join(visual_bits)}.")
    if isinstance(ctx.get("interests"), list):
        interests = [item.strip() for item in ctx["interests"] if isinstance(item, str) and item.strip()]
        if interests:
            details.append(f"Interests: {', '.join(interests[:4])}.")
    return " ".join(details)


def _merge_negative_prompt(*chunks: str) -> str:
    merged: list[str] = []
    seen: set[str] = set()
    for raw_chunk in [*chunks, DATASET_NEGATIVE_TERMS]:
        for term in raw_chunk.split(","):
            cleaned = term.strip()
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                merged.append(cleaned)
    return ", ".join(merged)


def _camera_distance(framing: str) -> str:
    return {"close_up_face": "tight_portrait", "medium": "editorial_mid", "full_body": "wide_full_body"}[framing]


def _quality_priority(framing: str, camera_angle: str, wardrobe_state: str) -> str:
    if framing == "full_body" and camera_angle in {"front", "left_three_quarter", "right_three_quarter"}:
        return "hero"
    if camera_angle in {"front", "left_three_quarter", "right_three_quarter"} or wardrobe_state == "clothed":
        return "standard"
    return "coverage"


def _build_variant_prompt(avatar_identity_block: str, shot: dict[str, str]) -> str:
    direction = (
        f"{FRAMING_DESCRIPTIONS[shot['framing']]}, {ANGLE_DESCRIPTIONS[shot['camera_angle']]}, {WARDROBE_DESCRIPTIONS[shot['wardrobe_state']]}, "
        f"{shot['pose_family'].replace('_', ' ')}, {shot['expression']}, {shot['camera_distance'].replace('_', ' ')}, "
        f"{shot['lens_hint']}, {shot['lighting_setup']}, {shot['background_style']}."
    )
    return _join_parts(avatar_identity_block, DATASET_REALISM_BLOCK, direction, QUALITY_GUARD_BLOCK)


def _iter_render_specs() -> list[dict[str, str]]:
    specs: list[dict[str, str]] = []
    sequence = 0
    for camera_angle, combo_counts in ANGLE_RENDER_COUNTS.items():
        for (framing, wardrobe_state), count in combo_counts.items():
            poses, expressions, lenses = POSE_CATALOG[(framing, wardrobe_state)], EXPRESSION_CATALOG[framing], LENS_HINTS[framing]
            for iteration in range(count):
                idx = sequence + iteration
                specs.append(
                    {
                        "framing": framing,
                        "wardrobe_state": wardrobe_state,
                        "camera_angle": camera_angle,
                        "pose_family": poses[idx % len(poses)],
                        "expression": expressions[idx % len(expressions)],
                        "camera_distance": _camera_distance(framing),
                        "lens_hint": lenses[idx % len(lenses)],
                        "lighting_setup": LIGHTING_CATALOG[idx % len(LIGHTING_CATALOG)],
                        "background_style": BACKGROUND_CATALOG[idx % len(BACKGROUND_CATALOG)],
                    }
                )
            sequence += count
    return specs


def build_dataset_shot_plan(*, dataset_version: str, avatar_identity_block: str, base_negative_prompt: str, seed_bundle: SeedBundle, samples_target: int = DEFAULT_RENDER_SAMPLES_TARGET, realism_profile: str = DEFAULT_REALISM_PROFILE, source_strategy: str = DEFAULT_SOURCE_STRATEGY) -> list[DatasetShot]:
    if isinstance(seed_bundle, dict):
        seed_bundle = SeedBundle.model_validate(seed_bundle)
    if samples_target != DEFAULT_RENDER_SAMPLES_TARGET:
        raise ValueError("samples_target must be 80 for the curated render shot planner")
    negative_prompt = _merge_negative_prompt(base_negative_prompt)
    shots: list[DatasetShot] = []
    for shot_index, spec in enumerate(_iter_render_specs(), start=1):
        class_name = "SFW" if spec["wardrobe_state"] == "clothed" else "NSFW"
        shots.append(
            DatasetShot(
                shot_index=shot_index,
                sample_id=f"{dataset_version}-{shot_index:03d}",
                class_name=class_name,
                wardrobe_state=spec["wardrobe_state"],
                framing=spec["framing"],
                shot_type=spec["framing"],
                camera_angle=spec["camera_angle"],
                pose_family=spec["pose_family"],
                expression=spec["expression"],
                camera_distance=spec["camera_distance"],
                lens_hint=spec["lens_hint"],
                lighting_setup=spec["lighting_setup"],
                background_style=spec["background_style"],
                quality_priority=_quality_priority(spec["framing"], spec["camera_angle"], spec["wardrobe_state"]),
                prompt=_build_variant_prompt(avatar_identity_block, spec),
                negative_prompt=negative_prompt,
                caption=f"adult real person, {spec['framing'].replace('_', ' ')}, {spec['camera_angle'].replace('_', ' ')}, {spec['wardrobe_state']}, {spec['pose_family'].replace('_', ' ')}, {spec['lens_hint']}, {spec['lighting_setup']}, photorealistic reference photo",
                seed=_dataset_sample_seed(seed_bundle.dataset_seed, shot_index),
                realism_profile=realism_profile,
                source_strategy=source_strategy,
            )
        )
    return shots


def _file_entry(identity_id: str, character_id: str, shot: DatasetShot) -> dict:
    return {
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
        "camera_distance": shot.camera_distance,
        "lens_hint": shot.lens_hint,
        "lighting_setup": shot.lighting_setup,
        "background_style": shot.background_style,
        "quality_priority": shot.quality_priority,
        "prompt": shot.prompt,
        "negative_prompt": shot.negative_prompt,
        "caption": shot.caption,
        "seed": shot.seed,
        "realism_profile": shot.realism_profile,
        "source_strategy": shot.source_strategy,
    }


def _coverage_summary(files: list[dict]) -> dict:
    return {
        "angles": dict(Counter(str(entry.get("camera_angle")) for entry in files)),
        "framing": dict(Counter(str(entry.get("framing")) for entry in files)),
        "wardrobe_state": dict(Counter(str(entry.get("wardrobe_state")) for entry in files)),
        "quality_priority": dict(Counter(str(entry.get("quality_priority")) for entry in files)),
    }


def _seed_training_subset(render_shot_plan: list[DatasetShot], target: int) -> tuple[list[DatasetShot], list[str], dict[str, str]]:
    selected: list[DatasetShot] = []
    reasons: dict[str, str] = {}
    for combo, needed in TRAINING_COMBO_TARGETS.items():
        combo_candidates = [shot for shot in render_shot_plan if shot.framing == combo[0] and shot.wardrobe_state == combo[1]]
        combo_candidates.sort(key=lambda shot: (QUALITY_PRIORITY_WEIGHT[shot.quality_priority], ANGLE_PRIORITY[shot.camera_angle], -shot.shot_index), reverse=True)
        selected.extend(combo_candidates[:needed])
        for shot in combo_candidates[:needed]:
            reasons[shot.sample_id] = "seed_subset_combo_quota"
    selected = sorted(selected, key=lambda shot: shot.shot_index)[:target]
    selected_ids = {shot.sample_id for shot in selected}
    return selected, [shot.sample_id for shot in render_shot_plan if shot.sample_id not in selected_ids], reasons


def build_generation_manifest(payload: GenerationServiceInput) -> GenerationManifest:
    digest = _stable_digest({"identity_id": str(payload.identity_id), "identity_context": payload.identity_context, "workflow_id": payload.workflow_id, "workflow_version": payload.workflow_version, "base_model_id": payload.base_model_id, "seed_basis": payload.seed_basis or str(payload.identity_id), "render_samples_target": payload.render_samples_target, "training_samples_target": payload.training_samples_target, "selection_policy": payload.selection_policy, "realism_profile": payload.realism_profile, "source_strategy": payload.source_strategy})
    identity_summary = _identity_summary(payload.identity_context)
    prompt = _join_parts(
        f"Create a consistent identity dataset portrait for {identity_summary}. Preserve premium visual coherence, natural anatomy, face consistency, full body fidelity, and reusable LoRA training coverage.",
        f"Tone: {payload.identity_context.get('voice_tone') or payload.identity_context.get('style') or 'editorial'}.",
        _prompt_details(payload.identity_context),
        f"Workflow guidance: {payload.copilot_prompt_template}." if payload.copilot_prompt_template else "",
        f"Additional prompt hints: {'; '.join(_flatten_hint_values(payload.prompt_hints))}." if _flatten_hint_values(payload.prompt_hints) else "",
    )
    seed_bundle = SeedBundle(portrait_seed=_seed_from_digest(digest, 0), variation_seed=_seed_from_digest(digest, 1), dataset_seed=_seed_from_digest(digest, 2))
    dataset_version = _dataset_version_from_digest(digest)
    negative_prompt = _bounded_text(_merge_negative_prompt(payload.copilot_negative_prompt or "", ", ".join(_flatten_hint_values(payload.negative_prompt_hints))), 1400)
    return GenerationManifest(
        identity_id=payload.identity_id,
        prompt=_bounded_text(prompt, 1200),
        negative_prompt=negative_prompt,
        seed_bundle=seed_bundle,
        samples_target=payload.training_samples_target,
        render_samples_target=payload.render_samples_target,
        training_samples_target=payload.training_samples_target,
        training_target_count=payload.training_samples_target,
        selection_policy=payload.selection_policy,
        workflow_id=payload.workflow_id,
        workflow_version=payload.workflow_version,
        workflow_family=payload.workflow_family,
        workflow_registry_source=payload.workflow_registry_source,
        base_model_id=payload.base_model_id,
        realism_profile=payload.realism_profile,
        source_strategy=payload.source_strategy,
        render_shot_plan=build_dataset_shot_plan(dataset_version=dataset_version, avatar_identity_block=_bounded_text(prompt, 1200), base_negative_prompt=negative_prompt, seed_bundle=seed_bundle, samples_target=payload.render_samples_target, realism_profile=payload.realism_profile, source_strategy=payload.source_strategy),
        comfy_parameters={"width": payload.image_width, "height": payload.image_height, "reference_face_image_url": payload.reference_face_image_url, "ip_adapter": payload.ip_adapter, "workflow_family": payload.workflow_family, "workflow_registry_source": payload.workflow_registry_source, "copilot_prompt_template": payload.copilot_prompt_template, "copilot_negative_prompt": payload.copilot_negative_prompt, "prompt_hints": payload.prompt_hints, "negative_prompt_hints": payload.negative_prompt_hints, "selection_policy": payload.selection_policy, "render_samples_target": payload.render_samples_target, "training_samples_target": payload.training_samples_target},
        artifact_path=str(PurePosixPath("artifacts") / "s1-llm" / str(payload.identity_id) / f"generation-manifest-{digest[:12]}.json"),
    )


def build_dataset_result(payload: DatasetServiceInput) -> dict:
    if payload.face_detection_confidence is None:
        raise ValueError("face_detection_confidence is required to validate dataset generation")
    render_shot_plan = payload.render_shot_plan or payload.generation_manifest.render_shot_plan
    if not render_shot_plan:
        raise ValueError("render_shot_plan is required to materialize the LoRA dataset manifest")
    character_id = str(payload.metadata_json.get("character_id") or payload.identity_id)
    seed_bundle = payload.generation_manifest.seed_bundle.model_dump(mode="json")
    dataset_version = render_shot_plan[0].sample_id.rsplit("-", 1)[0]
    identity_root = PurePosixPath(payload.artifact_root) / str(payload.identity_id) / "datasets" / dataset_version
    render_files = [_file_entry(str(payload.identity_id), character_id, shot) for shot in render_shot_plan]
    selected_shots, rejected_ids, selection_reasons = _seed_training_subset(render_shot_plan, payload.training_samples_target)
    selected_files = [_file_entry(str(payload.identity_id), character_id, shot) for shot in selected_shots]
    checksum = _stable_digest({"identity_id": str(payload.identity_id), "dataset_version": dataset_version, "selection_policy": payload.selection_policy})
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
            {"artifact_type": "base_image", "storage_path": str(identity_root / "base-image.png"), "content_type": "image/png", "metadata_json": {"identity_id": str(payload.identity_id), "character_id": character_id, "seed": payload.generation_manifest.seed_bundle.portrait_seed, "seed_bundle": seed_bundle, "face_detection_confidence": payload.face_detection_confidence, "realism_profile": payload.generation_manifest.realism_profile, "source_strategy": payload.generation_manifest.source_strategy, "workflow_family": payload.generation_manifest.workflow_family, "workflow_registry_source": payload.generation_manifest.workflow_registry_source}},
            {"artifact_type": "dataset_manifest", "storage_path": str(identity_root / "dataset-manifest.json"), "content_type": "application/json", "metadata_json": {"identity_id": str(payload.identity_id), "character_id": character_id, "seed_bundle": seed_bundle, "samples_target": payload.training_samples_target, "render_samples_target": payload.render_samples_target, "reference_face_image_url": payload.reference_face_image_url, "source_manifest_path": payload.generation_manifest.artifact_path, "workflow_extensions": workflow_extensions, "realism_profile": payload.generation_manifest.realism_profile, "source_strategy": payload.generation_manifest.source_strategy, "workflow_family": payload.generation_manifest.workflow_family, "workflow_registry_source": payload.generation_manifest.workflow_registry_source, "selection_policy": payload.selection_policy}},
            {"artifact_type": "dataset_package", "storage_path": str(identity_root / "dataset-package.zip"), "content_type": "application/zip", "checksum_sha256": checksum, "metadata_json": {"identity_id": str(payload.identity_id), "character_id": character_id, "seed_bundle": seed_bundle, "samples_target": payload.training_samples_target, "render_samples_target": payload.render_samples_target, "seed": payload.generation_manifest.seed_bundle.dataset_seed, "workflow_extensions": workflow_extensions, "realism_profile": payload.generation_manifest.realism_profile, "source_strategy": payload.generation_manifest.source_strategy, "workflow_family": payload.generation_manifest.workflow_family, "workflow_registry_source": payload.generation_manifest.workflow_registry_source, "selection_policy": payload.selection_policy, "render_manifest_path": str(identity_root / "render-manifest.json"), "render_package_path": str(identity_root / "render-package.zip")}},
        ],
        "dataset_manifest": {
            "schema_version": "1.2.0",
            "identity_id": str(payload.identity_id),
            "character_id": character_id,
            "dataset_version": dataset_version,
            "artifact_path": str(identity_root / "dataset-manifest.json"),
            "dataset_package_path": str(identity_root / "dataset-package.zip"),
            "render_manifest_path": str(identity_root / "render-manifest.json"),
            "render_package_path": str(identity_root / "render-package.zip"),
            "sample_count": payload.training_samples_target,
            "generated_samples": payload.training_samples_target,
            "render_sample_count": payload.render_samples_target,
            "selected_sample_count": payload.training_samples_target,
            "composition": {"policy": "balanced_50_50_curated", "SFW": sum(1 for entry in selected_files if entry["class_name"] == "SFW"), "NSFW": sum(1 for entry in selected_files if entry["class_name"] == "NSFW")},
            "render_composition": {"policy": "balanced_50_50_render", "SFW": sum(1 for entry in render_files if entry["class_name"] == "SFW"), "NSFW": sum(1 for entry in render_files if entry["class_name"] == "NSFW")},
            "files": selected_files,
            "render_files": render_files,
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
            "selection_policy": payload.selection_policy,
            "selection_reasons": selection_reasons,
            "rejected_sample_ids": rejected_ids,
            "coverage_summary": {"selected": _coverage_summary(selected_files), "rendered": _coverage_summary(render_files)},
        },
    }


def build_lora_training_result(payload: LoraTrainingServiceInput) -> dict:
    if payload.model_family != "flux":
        raise ValueError("lora training only supports the flux model family")
    dataset_locator = payload.dataset_package_path or json.dumps(payload.dataset_manifest, sort_keys=True)
    digest = _stable_digest({"identity_id": str(payload.identity_id), "dataset_locator": dataset_locator, "base_model_id": payload.base_model_id, "training_config": payload.training_config})
    identity_root = PurePosixPath(payload.artifact_root) / str(payload.identity_id)
    lora_path = str(identity_root / f"lora-model-{digest[:12]}.safetensors")
    manifest_path = str(identity_root / f"training-result-{digest[:12]}.json")
    checksum = _stable_digest({"lora_path": lora_path, "digest": digest})
    trigger_word = payload.training_config.get("trigger_word") or f"vb_{str(payload.identity_id).replace('-', '')[:8]}"
    steps = int(payload.training_config.get("training_steps", 1200))
    return {"provider": "modal", "service": "s1_lora_train", "base_model_id": payload.base_model_id, "model_family": payload.model_family, "artifacts": [{"artifact_type": "lora_model", "storage_path": lora_path, "content_type": "application/octet-stream", "checksum_sha256": checksum, "metadata_json": {"training_steps": steps, "trigger_word": trigger_word, "result_manifest_path": manifest_path}}], "training_manifest": {"identity_id": str(payload.identity_id), "base_model_id": payload.base_model_id, "dataset_package_path": payload.dataset_package_path, "dataset_manifest": payload.dataset_manifest, "dataset_source": {"handoff_mode": "dataset_package_path" if payload.dataset_package_path else "dataset_manifest", "dataset_locator": dataset_locator}, "training_steps": steps, "trigger_word": trigger_word, "result_manifest_path": manifest_path, "lora_model_path": lora_path, "checksum_sha256": checksum, "model_registry": {"version_name": f"lora-{digest[:8]}", "display_name": f"S1 LoRA {str(payload.identity_id)[:8]}", "base_model_id": payload.base_model_id, "storage_path": lora_path, "provider": "modal", "compatibility_notes": "Flux.1 Schnell compliant"}}}
