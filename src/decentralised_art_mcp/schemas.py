from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from .errors import ValidationError


ANY_SCHEMA: Dict[str, Any] = {}


def string_schema(*, min_length: Optional[int] = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {"type": "string"}
    if min_length is not None:
        schema["minLength"] = int(min_length)
    return schema


def integer_schema(*, minimum: Optional[int] = None, maximum: Optional[int] = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {"type": "integer"}
    if minimum is not None:
        schema["minimum"] = int(minimum)
    if maximum is not None:
        schema["maximum"] = int(maximum)
    return schema


def number_schema(*, minimum: Optional[float] = None, maximum: Optional[float] = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {"type": "number"}
    if minimum is not None:
        schema["minimum"] = float(minimum)
    if maximum is not None:
        schema["maximum"] = float(maximum)
    return schema


def boolean_schema() -> Dict[str, Any]:
    return {"type": "boolean"}


def object_schema(properties: Optional[Dict[str, Dict[str, Any]]] = None, *, required: Iterable[str] = (), additional_properties: bool = True) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": properties or {},
        "required": list(required),
        "additionalProperties": bool(additional_properties),
    }


def array_schema(items: Optional[Dict[str, Any]] = None, *, min_items: Optional[int] = None, max_items: Optional[int] = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {"type": "array"}
    if items is not None:
        schema["items"] = items
    if min_items is not None:
        schema["minItems"] = int(min_items)
    if max_items is not None:
        schema["maxItems"] = int(max_items)
    return schema


def _matches_type(expected: str, value: Any) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return True


def validate_payload(schema: Dict[str, Any], payload: Any, *, path: str = "payload") -> None:
    if not schema:
        return

    expected_type = schema.get("type")
    if expected_type and not _matches_type(expected_type, payload):
        raise ValidationError(f"{path} must be of type {expected_type}", details={"path": path, "expected_type": expected_type})

    if expected_type == "string":
        assert isinstance(payload, str)
        min_length = schema.get("minLength")
        if min_length is not None and len(payload) < int(min_length):
            raise ValidationError(
                f"{path} must contain at least {int(min_length)} characters",
                details={"path": path, "min_length": int(min_length)},
            )
        return

    if expected_type in {"integer", "number"}:
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and payload < minimum:
            raise ValidationError(f"{path} must be >= {minimum}", details={"path": path, "minimum": minimum})
        if maximum is not None and payload > maximum:
            raise ValidationError(f"{path} must be <= {maximum}", details={"path": path, "maximum": maximum})
        return

    if expected_type == "object":
        assert isinstance(payload, dict)
        properties = schema.get("properties") or {}
        required = schema.get("required") or []
        additional_properties = schema.get("additionalProperties", True)

        for key in required:
            if key not in payload:
                raise ValidationError(f"{path}.{key} is required", details={"path": f"{path}.{key}", "required": True})

        if not additional_properties:
            allowed = set(properties.keys())
            extras = sorted(key for key in payload.keys() if key not in allowed)
            if extras:
                raise ValidationError(
                    f"{path} contains unsupported properties: {extras}",
                    details={"path": path, "unsupported_properties": extras},
                )

        for key, child_schema in properties.items():
            if key in payload:
                validate_payload(child_schema, payload[key], path=f"{path}.{key}")
        return

    if expected_type == "array":
        assert isinstance(payload, list)
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if min_items is not None and len(payload) < int(min_items):
            raise ValidationError(f"{path} must contain at least {int(min_items)} items", details={"path": path, "min_items": int(min_items)})
        if max_items is not None and len(payload) > int(max_items):
            raise ValidationError(f"{path} must contain at most {int(max_items)} items", details={"path": path, "max_items": int(max_items)})
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(payload):
                validate_payload(item_schema, item, path=f"{path}[{index}]")
