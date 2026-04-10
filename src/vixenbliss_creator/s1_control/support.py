from __future__ import annotations

import hashlib
import os
import struct
import zlib
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_local_env() -> None:
    env_path = repo_root() / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def placeholder_png_bytes(*, width: int = 64, height: int = 64, rgba: tuple[int, int, int, int] = (155, 94, 118, 255)) -> bytes:
    if width <= 0 or height <= 0:
        raise ValueError("PNG dimensions must be positive integers")
    pixel = bytes(rgba)
    raw_scanlines = b"".join((b"\x00" + pixel * width) for _ in range(height))
    compressed = zlib.compress(raw_scanlines)

    def _chunk(chunk_type: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + chunk_type
            + payload
            + struct.pack(">I", zlib.crc32(chunk_type + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            _chunk(b"IHDR", ihdr),
            _chunk(b"IDAT", compressed),
            _chunk(b"IEND", b""),
        )
    )


def tiny_png_bytes() -> bytes:
    return placeholder_png_bytes()


def is_png_bytes(payload: bytes) -> bool:
    return payload.startswith(b"\x89PNG\r\n\x1a\n")


def png_dimensions(payload: bytes) -> tuple[int, int] | None:
    if not is_png_bytes(payload) or len(payload) < 24:
        return None
    return struct.unpack(">II", payload[16:24])


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
