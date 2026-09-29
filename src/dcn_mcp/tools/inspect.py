from __future__ import annotations

from typing import Any, Dict

from ..lifecycle import execution_particles
from ..inspect import group_samples_by_parent_with_diagnostics, summarize_samples


def register(registry) -> None:
    @registry.tool(
        namespace="inspect",
        name="group_execution_tree",
        description="Group raw execute samples by parent path and leaf name.",
        input_schema={"type": "object", "properties": {"samples": {"type": "array"}, "execution": {"type": "object"}}},
    )
    def _group(params: Dict[str, Any]) -> Dict[str, Any]:
        grouped, unknown_paths, diagnostics = group_samples_by_parent_with_diagnostics(execution_particles(params.get("execution", params.get("samples"))))
        return {"grouped": grouped, "unknown_paths": unknown_paths, "diagnostics": diagnostics, "provenance": _provenance(params)}

    @registry.tool(
        namespace="inspect",
        name="summarize_execution",
        description="Summarize raw execute samples without assuming a specific format family.",
        input_schema={"type": "object", "properties": {"samples": {"type": "array"}, "execution": {"type": "object"}}},
    )
    def _summarize(params: Dict[str, Any]) -> Dict[str, Any]:
        return {"summary": summarize_samples(execution_particles(params.get("execution", params.get("samples")))), "provenance": _provenance(params)}


def _provenance(params):
    source = params.get("execution")
    return {key: source[key] for key in ("block_number", "block_hash", "runner")} if source else None
