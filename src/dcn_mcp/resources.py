from __future__ import annotations

import pathlib
from typing import Dict, List

from .errors import ResourceNotFoundError
from .models import ResourceSpec


RESOURCE_URI_PREFIX = "dcn://resource/"


def resource_uri(name: str) -> str:
    return f"{RESOURCE_URI_PREFIX}{name}"


def resource_name_from_uri(uri: str) -> str:
    value = str(uri).strip()
    if value.startswith(RESOURCE_URI_PREFIX):
        return value[len(RESOURCE_URI_PREFIX):]
    return value


class ResourceRegistry:
    def __init__(self) -> None:
        self._resources: Dict[str, ResourceSpec] = {}

    def register(self, spec: ResourceSpec) -> ResourceSpec:
        if spec.name in self._resources:
            raise ValueError(f"Duplicate resource registration: {spec.name}")
        self._resources[spec.name] = spec
        return spec

    def register_markdown(self, *, name: str, description: str, path: pathlib.Path) -> ResourceSpec:
        return self.register(ResourceSpec(name=name, description=description, mime_type="text/markdown", file_path=path))

    def describe_resources(self) -> List[dict]:
        out = []
        for name in sorted(self._resources.keys()):
            described = self._resources[name].describe()
            described["uri"] = resource_uri(name)
            out.append(described)
        return out

    def read(self, name_or_uri: str) -> Dict[str, str]:
        name = resource_name_from_uri(name_or_uri)
        if name not in self._resources:
            raise ResourceNotFoundError(f"Unknown resource: {name_or_uri}", details={"name": name_or_uri})
        spec = self._resources[name]
        return {
            "name": spec.name,
            "uri": resource_uri(spec.name),
            "description": spec.description,
            "mime_type": spec.mime_type,
            "text": spec.file_path.read_text(encoding="utf-8"),
        }
