from __future__ import annotations

import math
import os
from dataclasses import dataclass


DEFAULT_TIMEOUT_SECONDS = 15.0
MIN_TIMEOUT_SECONDS = 0.1
MAX_TIMEOUT_SECONDS = 120.0


def parse_timeout(value: object, *, default: float = DEFAULT_TIMEOUT_SECONDS) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        parsed = float(text)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(parsed) or parsed < MIN_TIMEOUT_SECONDS or parsed > MAX_TIMEOUT_SECONDS:
        return default
    return parsed


def _env_string(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip() or default


DEFAULT_API_BASE = _env_string("API_BASE", "https://api.decentralised.art/chain")
DEFAULT_TIMEOUT = parse_timeout(os.getenv("DCN_TIMEOUT"))
DEFAULT_ARTIFACT_ROOT = _env_string("DCN_ARTIFACT_ROOT", "dcn-mcp-artifacts")
DEFAULT_PREFERRED_TRANSFORMATION_PAIRS = (
    ("math_add_v1", "math_subtract_v1"),
    ("add", "subtract"),
)


@dataclass(frozen=True)
class RuntimeConfig:
    api_base: str = DEFAULT_API_BASE
    timeout: float = DEFAULT_TIMEOUT
