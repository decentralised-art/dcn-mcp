from __future__ import annotations

from typing import Any, Dict

from ..artifacts import resolve_artifact_path, write_json, write_jsonl
from ..schemas import ANY_SCHEMA, array_schema, object_schema, string_schema


def register(registry) -> None:
    @registry.tool(
        namespace="artifacts",
        name="write_json",
        description="Write one JSON artifact to disk.",
        input_schema=object_schema({"path": string_schema(), "payload": ANY_SCHEMA}, required=["path", "payload"]),
    )
    def _write_json(params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_artifact_path(params["path"])
        return {"path": write_json(path, params["payload"])}

    @registry.tool(
        namespace="artifacts",
        name="write_jsonl",
        description="Write newline-delimited JSON records to disk.",
        input_schema=object_schema({"path": string_schema(), "records": array_schema()}, required=["path", "records"]),
    )
    def _write_jsonl(params: Dict[str, Any]) -> Dict[str, Any]:
        path = resolve_artifact_path(params["path"])
        return {"path": write_jsonl(path, list(params["records"]))}
