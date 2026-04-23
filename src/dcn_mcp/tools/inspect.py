from __future__ import annotations

from typing import Any, Dict

from ..inspect import group_samples_by_parent, summarize_samples


def register(registry) -> None:
    @registry.tool(
        namespace="inspect",
        name="group_execution_tree",
        description="Group raw execute samples by parent path and leaf name.",
        input_schema={"type": "object", "properties": {"samples": {"type": "array"}}, "required": ["samples"]},
    )
    def _group(params: Dict[str, Any]) -> Dict[str, Any]:
        grouped, unknown_paths = group_samples_by_parent(list(params["samples"]))
        return {"grouped": grouped, "unknown_paths": unknown_paths}

    @registry.tool(
        namespace="inspect",
        name="summarize_execution",
        description="Summarize raw execute samples without assuming a specific format family.",
        input_schema={"type": "object", "properties": {"samples": {"type": "array"}}, "required": ["samples"]},
    )
    def _summarize(params: Dict[str, Any]) -> Dict[str, Any]:
        return {"summary": summarize_samples(list(params["samples"]))}
