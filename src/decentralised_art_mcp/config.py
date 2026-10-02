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


# Settings named before the decentralised.art rename are still read when the new ones are
# unset, so existing setups and their publication records keep working.
LEGACY_SETTINGS = {
    "DECENTRALISED_ART_TIMEOUT": "DCN_TIMEOUT",
    "DECENTRALISED_ART_ARTIFACT_ROOT": "DCN_ARTIFACT_ROOT",
}
ARTIFACT_ROOT_FOLDER = "decentralised-art-mcp-artifacts"
LEGACY_ARTIFACT_ROOT_FOLDER = "dcn-mcp-artifacts"


def _setting(name: str) -> str | None:
    value = os.getenv(name)
    if value is not None and value.strip():
        return value
    legacy = LEGACY_SETTINGS.get(name)
    return os.getenv(legacy) if legacy else value


def default_artifact_root() -> str:
    configured = (_setting("DECENTRALISED_ART_ARTIFACT_ROOT") or "").strip()
    if configured:
        return configured
    # Never lose existing publication records: they prevent a pending publication from
    # being sent twice.
    if not os.path.exists(ARTIFACT_ROOT_FOLDER) and os.path.isdir(LEGACY_ARTIFACT_ROOT_FOLDER):
        return LEGACY_ARTIFACT_ROOT_FOLDER
    return ARTIFACT_ROOT_FOLDER


DEFAULT_API_BASE = _env_string("API_BASE", "https://api.decentralised.art/chain")
DEFAULT_TIMEOUT = parse_timeout(_setting("DECENTRALISED_ART_TIMEOUT"))
DEFAULT_ARTIFACT_ROOT = default_artifact_root()
DEFAULT_PREFERRED_TRANSFORMATION_PAIRS = (
    ("math_add_v1", "math_subtract_v1"),
    ("add", "subtract"),
)


@dataclass(frozen=True)
class RuntimeConfig:
    api_base: str = DEFAULT_API_BASE
    timeout: float = DEFAULT_TIMEOUT
