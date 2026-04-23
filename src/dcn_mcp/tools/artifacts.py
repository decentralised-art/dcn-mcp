from __future__ import annotations

import pathlib
from typing import Any, Dict, Iterable, List

from ..artifacts import write_json, write_jsonl


def register(registry) -> None:
    @registry.tool(
        namespace="artifacts",
        name="write_json",
        description="Write one JSON artifact to disk.",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}, "payload": {}}, "required": ["path", "payload"]},
    )
    def _write_json(params: Dict[str, Any]) -> Dict[str, Any]:
        path = pathlib.Path(str(params["path"])).resolve()
        return {"path": write_json(path, params["payload"])}

    @registry.tool(
        namespace="artifacts",
        name="write_jsonl",
        description="Write newline-delimited JSON records to disk.",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}, "records": {"type": "array"}}, "required": ["path", "records"]},
    )
    def _write_jsonl(params: Dict[str, Any]) -> Dict[str, Any]:
        path = pathlib.Path(str(params["path"])).resolve()
        return {"path": write_jsonl(path, list(params["records"]))}
