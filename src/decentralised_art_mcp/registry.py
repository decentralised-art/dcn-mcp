from __future__ import annotations

from typing import Any, Callable, Dict, List

from .errors import ToolNotFoundError, error_to_payload
from .models import ToolSpec
from .schemas import validate_payload


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> ToolSpec:
        if spec.full_name in self._tools:
            raise ValueError(f"Duplicate tool registration: {spec.full_name}")
        self._tools[spec.full_name] = spec
        return spec

    def tool(self, *, namespace: str, name: str, description: str, input_schema: Dict[str, Any]) -> Callable[[Callable[[Dict[str, Any]], Any]], Callable[[Dict[str, Any]], Any]]:
        def decorator(handler: Callable[[Dict[str, Any]], Any]) -> Callable[[Dict[str, Any]], Any]:
            self.register(ToolSpec(name=name, namespace=namespace, description=description, input_schema=input_schema, handler=handler))
            return handler
        return decorator

    def describe_tools(self) -> List[Dict[str, Any]]:
        return [self._tools[name].describe() for name in sorted(self._tools.keys())]

    def invoke(self, full_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if full_name not in self._tools:
                raise ToolNotFoundError(f"Unknown tool: {full_name}", details={"tool_name": full_name})
            spec = self._tools[full_name]
            validate_payload(spec.input_schema, params, path="params")
            result = spec.handler(params)
            return {"ok": True, "data": result}
        except Exception as exc:
            return {"ok": False, "error": error_to_payload(exc)}
