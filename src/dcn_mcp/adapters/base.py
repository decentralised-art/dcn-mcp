from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable

from ..registry import ToolRegistry
from ..resources import ResourceRegistry


class FormatAdapter(ABC):
    name: str
    description: str

    @abstractmethod
    def supports_leaves(self, leaves: Iterable[str]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def register_tools(self, registry: ToolRegistry) -> None:
        raise NotImplementedError

    def register_resources(self, registry: ResourceRegistry) -> None:
        return None

    def describe(self) -> Dict[str, str]:
        return {"name": self.name, "description": self.description}
