from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_API_BASE = os.getenv("API_BASE", "https://api.decentralised.art/chain")
DEFAULT_TIMEOUT = float(os.getenv("DCN_TIMEOUT", "15"))
DEFAULT_PREFERRED_TRANSFORMATION_PAIRS = (
    ("math_add_v1", "math_subtract_v1"),
    ("add", "subtract"),
)


@dataclass(frozen=True)
class RuntimeConfig:
    api_base: str = DEFAULT_API_BASE
    timeout: float = DEFAULT_TIMEOUT
