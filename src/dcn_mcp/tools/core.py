from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple

from ..config import DEFAULT_PREFERRED_TRANSFORMATION_PAIRS, MAX_TIMEOUT_SECONDS, MIN_TIMEOUT_SECONDS
from ..context import context_from_params
from ..errors import ValidationError
from ..schemas import array_schema, boolean_schema, integer_schema, number_schema, object_schema, string_schema

MAX_PAGE_LIMIT = 256
MAX_STREAM_REPLAY_LIMIT = 2048
MAX_PARTICLES_COUNT = 65536

TIMEOUT_SCHEMA = number_schema(minimum=MIN_TIMEOUT_SECONDS, maximum=MAX_TIMEOUT_SECONDS)
PAGE_LIMIT_SCHEMA = integer_schema(minimum=1, maximum=MAX_PAGE_LIMIT)
STREAM_REPLAY_LIMIT_SCHEMA = integer_schema(minimum=1, maximum=MAX_STREAM_REPLAY_LIMIT)
PARTICLES_COUNT_SCHEMA = integer_schema(minimum=1, maximum=MAX_PARTICLES_COUNT)
TRANSFORMATION_PAIR_SCHEMA = array_schema(string_schema(min_length=1), min_items=2, max_items=2)
TRANSFORMATION_PAIRS_SCHEMA = array_schema(TRANSFORMATION_PAIR_SCHEMA, min_items=1)


def _optional_int(params: Dict[str, Any], key: str, *, default: int, minimum: int, maximum: int) -> int:
    if key not in params or params[key] is None:
        return default
    value = params[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"params.{key} must be an integer.", details={"path": f"params.{key}", "expected_type": "integer"})
    if value < minimum or value > maximum:
        raise ValidationError(f"params.{key} must be between {minimum} and {maximum}.", details={"path": f"params.{key}", "minimum": minimum, "maximum": maximum})
    return value


def _transformation_pairs(value: Any, *, field_name: str, default: Iterable[Tuple[str, str]]) -> List[Tuple[str, str]]:
    raw = list(default) if value is None else value
    if not isinstance(raw, (list, tuple)) or isinstance(raw, (str, bytes)):
        raise ValidationError(f"params.{field_name} must be an array of [add, subtract] pairs.", details={"path": f"params.{field_name}"})
    if len(raw) == 0:
        raise ValidationError(f"params.{field_name} must include at least one pair.", details={"path": f"params.{field_name}", "min_items": 1})
    pairs: List[Tuple[str, str]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, (list, tuple)) or isinstance(item, (str, bytes)) or len(item) != 2:
            raise ValidationError(
                f"params.{field_name}[{index}] must contain exactly two names.",
                details={"path": f"params.{field_name}[{index}]", "expected_items": 2},
            )
        add, subtract = str(item[0]).strip(), str(item[1]).strip()
        if not add or not subtract:
            raise ValidationError(
                f"params.{field_name}[{index}] names must be non-empty strings.",
                details={"path": f"params.{field_name}[{index}]"},
            )
        pairs.append((add, subtract))
    return pairs


def build_parent_connector(child_names: Sequence[str], *, name: str) -> Dict[str, Any]:
    return {
        "name": str(name),
        "dimensions": [{"transformations": [], "composite": child_name, "bindings": {}} for child_name in child_names],
        "condition_name": "",
        "condition_args": [],
        "static_ri": {},
    }


def register(registry) -> None:
    @registry.tool(
        namespace="core",
        name="connector_exists",
        description="Check whether a connector exists on the DCN.",
        input_schema=object_schema({"name": string_schema(min_length=1), "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}, required=["name"]),
    )
    def _connector_exists(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return {"name": params["name"], "exists": ctx.client().connector_exists(str(params["name"]))}

    @registry.tool(
        namespace="core",
        name="get_nonce",
        description="Fetch the current auth nonce for an address.",
        input_schema=object_schema({"address": string_schema(min_length=1), "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}, required=["address"]),
    )
    def _get_nonce(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return {"address": params["address"], "nonce": ctx.client().get_nonce(str(params["address"]))}

    @registry.tool(
        namespace="core",
        name="get_connector",
        description="Fetch a connector payload by name.",
        input_schema=object_schema({"name": string_schema(min_length=1), "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}, required=["name"]),
    )
    def _get_connector(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return ctx.client().get_connector(str(params["name"]))

    @registry.tool(
        namespace="core",
        name="get_transformation",
        description="Fetch a transformation payload by name.",
        input_schema=object_schema({"name": string_schema(min_length=1), "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}, required=["name"]),
    )
    def _get_transformation(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return ctx.client().get_transformation(str(params["name"]))

    @registry.tool(
        namespace="core",
        name="get_condition",
        description="Fetch a condition payload by name.",
        input_schema=object_schema({"name": string_schema(min_length=1), "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}, required=["name"]),
    )
    def _get_condition(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return ctx.client().get_condition(str(params["name"]))

    @registry.tool(
        namespace="core",
        name="transformation_exists",
        description="Check whether a transformation exists on the DCN.",
        input_schema=object_schema({"name": string_schema(min_length=1), "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}, required=["name"]),
    )
    def _transformation_exists(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return {"name": params["name"], "exists": ctx.client().transformation_exists(str(params["name"]))}

    @registry.tool(
        namespace="core",
        name="condition_exists",
        description="Check whether a condition exists on the DCN.",
        input_schema=object_schema({"name": string_schema(min_length=1), "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}, required=["name"]),
    )
    def _condition_exists(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return {"name": params["name"], "exists": ctx.client().condition_exists(str(params["name"]))}

    @registry.tool(
        namespace="core",
        name="get_feed_page",
        description="Fetch a page from the DCN event feed.",
        input_schema=object_schema(
            {
                "limit": PAGE_LIMIT_SCHEMA,
                "before": string_schema(),
                "type": string_schema(),
                "include_unfinalized": boolean_schema(),
                "api_base": string_schema(),
                "timeout": TIMEOUT_SCHEMA,
            },
        ),
    )
    def _get_feed_page(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return ctx.client().get_feed_page(
                limit=_optional_int(params, "limit", default=100, minimum=1, maximum=MAX_PAGE_LIMIT),
                before=params.get("before"),
                event_type=params.get("type"),
                include_unfinalized=params.get("include_unfinalized"),
            )

    @registry.tool(
        namespace="core",
        name="get_feed_stream_replay",
        description="Read a bounded replay from the DCN event feed SSE stream.",
        input_schema=object_schema(
            {
                "since_seq": integer_schema(minimum=0),
                "limit": STREAM_REPLAY_LIMIT_SCHEMA,
                "api_base": string_schema(),
                "timeout": TIMEOUT_SCHEMA,
            },
        ),
    )
    def _get_feed_stream_replay(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return ctx.client().get_feed_stream_replay(
                since_seq=_optional_int(params, "since_seq", default=0, minimum=0, maximum=2**63 - 1),
                limit=_optional_int(params, "limit", default=200, minimum=1, maximum=MAX_STREAM_REPLAY_LIMIT),
            )

    @registry.tool(
        namespace="core",
        name="list_formats",
        description="List formats known to the DCN.",
        input_schema=object_schema({"limit": PAGE_LIMIT_SCHEMA, "after": string_schema(), "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}),
    )
    def _list_formats(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return ctx.client().list_formats(limit=_optional_int(params, "limit", default=100, minimum=1, maximum=MAX_PAGE_LIMIT), after=params.get("after"))

    @registry.tool(
        namespace="core",
        name="get_format",
        description="Fetch one format and its features.",
        input_schema=object_schema({"format_hash": string_schema(min_length=1), "limit": PAGE_LIMIT_SCHEMA, "after": string_schema(), "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}, required=["format_hash"]),
    )
    def _get_format(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return ctx.client().get_format(str(params["format_hash"]), limit=_optional_int(params, "limit", default=256, minimum=1, maximum=MAX_PAGE_LIMIT), after=params.get("after"))

    @registry.tool(
        namespace="core",
        name="get_account",
        description="Fetch account-owned connectors, transformations, and conditions for an address.",
        input_schema=object_schema(
            {
                "address": string_schema(min_length=1),
                "limit": PAGE_LIMIT_SCHEMA,
                "after_connectors": string_schema(),
                "after_transformations": string_schema(),
                "after_conditions": string_schema(),
                "api_base": string_schema(),
                "timeout": TIMEOUT_SCHEMA,
            },
            required=["address"],
        ),
    )
    def _get_account(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return ctx.client().get_account(
                str(params["address"]),
                limit=_optional_int(params, "limit", default=256, minimum=1, maximum=MAX_PAGE_LIMIT),
                after_connectors=params.get("after_connectors"),
                after_transformations=params.get("after_transformations"),
                after_conditions=params.get("after_conditions"),
            )

    @registry.tool(
        namespace="core",
        name="deploy_connector",
        description="Deploy a connector payload to the DCN.",
        input_schema=object_schema({"payload": object_schema(), "private_key": string_schema(), "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}, required=["payload"]),
    )
    def _deploy_connector(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return ctx.client().post_connector(dict(params["payload"]), ctx.account())

    @registry.tool(
        namespace="core",
        name="deploy_transformation",
        description="Deploy a transformation payload to the DCN.",
        input_schema=object_schema({"payload": object_schema(), "private_key": string_schema(), "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}, required=["payload"]),
    )
    def _deploy_transformation(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return ctx.client().post_transformation(dict(params["payload"]), ctx.account())

    @registry.tool(
        namespace="core",
        name="deploy_condition",
        description="Deploy a condition payload to the DCN.",
        input_schema=object_schema({"payload": object_schema(), "private_key": string_schema(), "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}, required=["payload"]),
    )
    def _deploy_condition(params: Dict[str, Any]) -> Dict[str, Any]:
        with context_from_params(params) as ctx:
            return ctx.client().post_condition(dict(params["payload"]), ctx.account())

    @registry.tool(
        namespace="core",
        name="execute_connector",
        description="Execute a connector and return raw samples.",
        input_schema=object_schema(
            {
                "connector_name": string_schema(min_length=1),
                "particles_count": PARTICLES_COUNT_SCHEMA,
                "dynamic_ri": object_schema(),
                "private_key": string_schema(),
                "api_base": string_schema(),
                "timeout": TIMEOUT_SCHEMA,
            },
            required=["connector_name", "particles_count"],
        ),
    )
    def _execute_connector(params: Dict[str, Any]) -> Dict[str, Any]:
        dynamic_ri = params["dynamic_ri"] if "dynamic_ri" in params and params["dynamic_ri"] is not None else {}
        with context_from_params(params) as ctx:
            samples = ctx.client().execute_connector(
                ctx.account(),
                connector_name=str(params["connector_name"]),
                particles_count=int(params["particles_count"]),
                dynamic_ri=dict(dynamic_ri),
            )
            return {"samples": samples}

    @registry.tool(
        namespace="core",
        name="resolve_transformation_pair",
        description="Resolve the first supported add/subtract transformation pair on the network.",
        input_schema=object_schema({"pairs": TRANSFORMATION_PAIRS_SCHEMA, "api_base": string_schema(), "timeout": TIMEOUT_SCHEMA}),
    )
    def _resolve_pair(params: Dict[str, Any]) -> Dict[str, Any]:
        pairs = _transformation_pairs(params.get("pairs"), field_name="pairs", default=DEFAULT_PREFERRED_TRANSFORMATION_PAIRS)
        with context_from_params(params) as ctx:
            pair = ctx.client().resolve_preferred_transformation_pair(pairs)
            return {"add": pair.add, "subtract": pair.subtract}

    @registry.tool(
        namespace="core",
        name="ensure_preflight",
        description="Authenticate, ensure required connectors exist, and resolve a preferred transformation pair.",
        input_schema=object_schema(
            {
                "required_connectors": array_schema(string_schema(min_length=1), min_items=1),
                "preferred_transformation_pairs": TRANSFORMATION_PAIRS_SCHEMA,
                "private_key": string_schema(),
                "api_base": string_schema(),
                "timeout": TIMEOUT_SCHEMA,
            },
            required=["required_connectors"],
        ),
    )
    def _ensure_preflight(params: Dict[str, Any]) -> Dict[str, Any]:
        pairs = _transformation_pairs(params.get("preferred_transformation_pairs"), field_name="preferred_transformation_pairs", default=DEFAULT_PREFERRED_TRANSFORMATION_PAIRS)
        with context_from_params(params) as ctx:
            acct = ctx.account()
            pair = ctx.client().ensure_preflight(
                acct,
                required_connectors=list(params["required_connectors"]),
                preferred_transformation_pairs=pairs,
            )
            return {"add": pair.add, "subtract": pair.subtract, "address": acct.address}

    @registry.tool(
        namespace="core",
        name="build_parent_connector",
        description="Build a generic structural parent connector over child connector names.",
        input_schema=object_schema({"name": string_schema(min_length=1), "child_names": array_schema(string_schema(min_length=1), min_items=1)}, required=["name", "child_names"]),
    )
    def _build_parent(params: Dict[str, Any]) -> Dict[str, Any]:
        return build_parent_connector(params["child_names"], name=params["name"])
