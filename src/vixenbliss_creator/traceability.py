from __future__ import annotations


def normalize_trace_source_text(
    value: object,
    *,
    max_length: int = 200,
    min_length: int = 3,
) -> str | None:
    candidate = " ".join(str(value or "").split())
    if not candidate:
        return None
    if len(candidate) > max_length:
        candidate = candidate[:max_length].rstrip(" ,;:-")
    if len(candidate) < min_length:
        return None
    return candidate
