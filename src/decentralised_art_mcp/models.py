from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class ChainCursor:
    has_more: bool
    next_after: Optional[str]


@dataclass
class TransformationPair:
    add: str
    subtract: str


@dataclass
class ToolSpec:
    name: str
    namespace: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Any] = field(repr=False)

    @property
    def full_name(self) -> str:
        return f"{self.namespace}.{self.name}"

    def describe(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "namespace": self.namespace,
            "full_name": self.full_name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class ResourceSpec:
    name: str
    description: str
    mime_type: str
    file_path: pathlib.Path = field(repr=False)

    def describe(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "mime_type": self.mime_type,
            "path": str(self.file_path),
        }
