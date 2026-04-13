from __future__ import annotations

import hashlib
import re


_FIRST_NAMES = (
    "Amber",
    "Bianca",
    "Clara",
    "Ivy",
    "Luna",
    "Mara",
    "Naomi",
    "Nora",
    "Selene",
    "Stella",
    "Vera",
    "Zoe",
)

_LAST_NAMES = (
    "Bloom",
    "Cross",
    "Frost",
    "Hart",
    "Lane",
    "Noir",
    "Quinn",
    "Rey",
    "Stone",
    "Vale",
    "Voss",
    "Wren",
)

_EXPLICIT_NAME_PATTERNS = (
    re.compile(r"\b(?:llamad[ao]|named|nombre)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"),
    re.compile(r"\b(?:avatar|modelo|personaje)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"),
)


def _normalized_idea(idea: str) -> str:
    return " ".join(str(idea or "").split())


def explicit_display_name_from_idea(idea: str) -> str | None:
    normalized = _normalized_idea(idea)
    if not normalized:
        return None
    for pattern in _EXPLICIT_NAME_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return match.group(1).strip()
    return None


def generated_display_name_from_idea(idea: str) -> str:
    normalized = _normalized_idea(idea).lower() or "vixenbliss"
    digest = hashlib.sha256(normalized.encode("utf-8")).digest()
    first_name = _FIRST_NAMES[digest[0] % len(_FIRST_NAMES)]
    last_name = _LAST_NAMES[digest[1] % len(_LAST_NAMES)]
    return f"{first_name} {last_name}"


def resolve_display_name(idea: str, explicit_name: object = None) -> str:
    candidate = _normalized_idea(str(explicit_name or ""))
    if candidate:
        return candidate
    inferred = explicit_display_name_from_idea(idea)
    if inferred:
        return inferred
    return generated_display_name_from_idea(idea)
