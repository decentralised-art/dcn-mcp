"""Runtime access to chain contracts generated from pinned dcn-api-spec OpenAPI."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib.resources import files
from typing import Any
from urllib.parse import quote

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as SchemaValidationError

from .errors import ValidationError


@lru_cache(maxsize=1)
def _document() -> dict[str, Any]:
    resource = files("dcn_mcp").joinpath("generated/api_contracts.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def spec_commit() -> str:
    return str(_document()["spec_commit"])


def _operation(operation_id: str) -> dict[str, Any]:
    try:
        return _document()["operations"][operation_id]
    except KeyError as exc:
        raise ValueError(f"Unknown dcn-api-spec operation: {operation_id}") from exc


def api_path(operation_id: str, **parameters: object) -> str:
    template = _operation(operation_id)["path"]
    used: set[str] = set()

    def substitute(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in parameters:
            raise ValueError(f"Missing {operation_id} path parameter: {name}")
        used.add(name)
        return quote(str(parameters[name]).strip(), safe="")

    path = re.sub(r"\{([^{}]+)\}", substitute, template)
    extra = parameters.keys() - used
    if extra:
        raise ValueError(f"Unexpected {operation_id} path parameters: {', '.join(sorted(extra))}")
    return path


def _validate(operation_id: str, field: str, payload: Any, schema: Any) -> None:
    if schema is None:
        raise ValueError(f"{operation_id} has no {field} in dcn-api-spec")
    try:
        Draft202012Validator(schema).validate(payload)
    except SchemaValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path)
        path = f"{field}.{location}" if location else field
        raise ValidationError(
            f"{operation_id} violates dcn-api-spec at {path}: {exc.message}",
            details={"operation": operation_id, "path": path},
        ) from exc


def validate_request(operation_id: str, payload: Any) -> None:
    _validate(operation_id, "request_schema", payload, _operation(operation_id)["request_schema"])


def validate_query(operation_id: str, params: dict[str, Any]) -> None:
    _validate(operation_id, "query_schema", params, _operation(operation_id)["query_schema"])


def validate_response(operation_id: str, payload: Any, status_code: int | None = None) -> None:
    schemas = _operation(operation_id)["response_schemas"]
    if status_code is None and len(schemas) == 1:
        status_code = int(next(iter(schemas)))
    if str(status_code) not in schemas:
        raise ValueError(f"{operation_id} has no documented JSON response for HTTP {status_code}")
    _validate(operation_id, f"response_schemas.{status_code}", payload, schemas[str(status_code)])
