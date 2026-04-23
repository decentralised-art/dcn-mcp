from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .base import FormatAdapter


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: Dict[str, FormatAdapter] = {}

    def register(self, adapter: FormatAdapter) -> FormatAdapter:
        if adapter.name in self._adapters:
            raise ValueError(f"Duplicate adapter registration: {adapter.name}")
        self._adapters[adapter.name] = adapter
        return adapter

    def describe(self) -> List[dict]:
        return [self._adapters[name].describe() for name in sorted(self._adapters.keys())]

    def get(self, name: str) -> Optional[FormatAdapter]:
        return self._adapters.get(name)

    def match(self, leaves: Iterable[str]) -> List[FormatAdapter]:
        normalized = list(leaves)
        return [adapter for adapter in self._adapters.values() if adapter.supports_leaves(normalized)]
