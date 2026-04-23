from __future__ import annotations

from typing import Sequence

from .client import DCNClient


def sanitize_name(name: str, *, prefix: str = "connector", max_len: int = 96) -> str:
    raw = str(name or "").strip()
    if not raw:
        raw = prefix
    out = "".join(char if char.isalnum() or char == "_" else "_" for char in raw)
    while "__" in out:
        out = out.replace("__", "_")
    out = out.strip("_") or prefix
    if not (out[0].isalpha() or out[0] == "_"):
        out = f"{prefix}_{out}"
    return out[:max_len]


def ensure_unique_name(dcn: DCNClient, name: str, reserved: Sequence[str]) -> str:
    base = sanitize_name(name)
    reserved_set = {str(item).strip() for item in reserved}
    candidate = base
    suffix = 2
    while candidate in reserved_set or dcn.connector_exists(candidate):
        candidate = sanitize_name(f"{base}_{suffix}")
        suffix += 1
    return candidate
