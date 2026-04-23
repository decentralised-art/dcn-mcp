from __future__ import annotations

from typing import Any, Dict, Sequence

from ..config import DEFAULT_PREFERRED_TRANSFORMATION_PAIRS
from ..context import context_from_params
from ..schemas import ANY_SCHEMA, array_schema, integer_schema, number_schema, object_schema, string_schema


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
        input_schema=object_schema({"name": string_schema(), "api_base": string_schema(), "timeout": number_schema()}, required=["name"]),
    )
    def _connector_exists(params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = context_from_params(params)
        return {"name": params["name"], "exists": ctx.client().connector_exists(str(params["name"]))}

    @registry.tool(
        namespace="core",
        name="get_nonce",
        description="Fetch the current auth nonce for an address.",
        input_schema=object_schema({"address": string_schema(), "api_base": string_schema(), "timeout": number_schema()}, required=["address"]),
    )
    def _get_nonce(params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = context_from_params(params)
        return {"address": params["address"], "nonce": ctx.client().get_nonce(str(params["address"]))}

    @registry.tool(
        namespace="core",
        name="get_connector",
        description="Fetch a connector payload by name.",
        input_schema=object_schema({"name": string_schema(), "api_base": string_schema(), "timeout": number_schema()}, required=["name"]),
    )
    def _get_connector(params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = context_from_params(params)
        return ctx.client().get_connector(str(params["name"]))

    @registry.tool(
        namespace="core",
        name="get_transformation",
        description="Fetch a transformation payload by name.",
        input_schema=object_schema({"name": string_schema(), "api_base": string_schema(), "timeout": number_schema()}, required=["name"]),
    )
    def _get_transformation(params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = context_from_params(params)
        return ctx.client().get_transformation(str(params["name"]))

    @registry.tool(
        namespace="core",
        name="transformation_exists",
        description="Check whether a transformation exists on the DCN.",
        input_schema=object_schema({"name": string_schema(), "api_base": string_schema(), "timeout": number_schema()}, required=["name"]),
    )
    def _transformation_exists(params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = context_from_params(params)
        return {"name": params["name"], "exists": ctx.client().transformation_exists(str(params["name"]))}

    @registry.tool(
        namespace="core",
        name="list_formats",
        description="List formats known to the DCN.",
        input_schema=object_schema({"limit": integer_schema(), "after": string_schema(), "api_base": string_schema(), "timeout": number_schema()}),
    )
    def _list_formats(params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = context_from_params(params)
        return ctx.client().list_formats(limit=int(params.get("limit") or 100), after=params.get("after"))

    @registry.tool(
        namespace="core",
        name="get_format",
        description="Fetch one format and its features.",
        input_schema=object_schema({"format_hash": string_schema(), "limit": integer_schema(), "after": string_schema(), "api_base": string_schema(), "timeout": number_schema()}, required=["format_hash"]),
    )
    def _get_format(params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = context_from_params(params)
        return ctx.client().get_format(str(params["format_hash"]), limit=int(params.get("limit") or 256), after=params.get("after"))

    @registry.tool(
        namespace="core",
        name="get_account",
        description="Fetch account-owned connectors, transformations, and conditions for an address.",
        input_schema=object_schema(
            {
                "address": string_schema(),
                "limit": integer_schema(),
                "after_connectors": string_schema(),
                "after_transformations": string_schema(),
                "after_conditions": string_schema(),
                "api_base": string_schema(),
                "timeout": number_schema(),
            },
            required=["address"],
        ),
    )
    def _get_account(params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = context_from_params(params)
        return ctx.client().get_account(
            str(params["address"]),
            limit=int(params.get("limit") or 256),
            after_connectors=params.get("after_connectors"),
            after_transformations=params.get("after_transformations"),
            after_conditions=params.get("after_conditions"),
        )

    @registry.tool(
        namespace="core",
        name="deploy_connector",
        description="Deploy a connector payload to the DCN.",
        input_schema=object_schema({"payload": object_schema(), "private_key": string_schema(), "api_base": string_schema(), "timeout": number_schema()}, required=["payload"]),
    )
    def _deploy_connector(params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = context_from_params(params)
        return ctx.client().post_connector(dict(params["payload"]), ctx.account())

    @registry.tool(
        namespace="core",
        name="execute_connector",
        description="Execute a connector and return raw samples.",
        input_schema=object_schema(
            {
                "connector_name": string_schema(),
                "particles_count": integer_schema(),
                "dynamic_ri": object_schema(),
                "private_key": string_schema(),
                "api_base": string_schema(),
                "timeout": number_schema(),
            },
            required=["connector_name", "particles_count"],
        ),
    )
    def _execute_connector(params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = context_from_params(params)
        samples = ctx.client().execute_connector(
            ctx.account(),
            connector_name=str(params["connector_name"]),
            particles_count=int(params["particles_count"]),
            dynamic_ri=dict(params.get("dynamic_ri") or {}),
        )
        return {"samples": samples}

    @registry.tool(
        namespace="core",
        name="resolve_transformation_pair",
        description="Resolve the first supported add/subtract transformation pair on the network.",
        input_schema=object_schema({"pairs": array_schema(), "api_base": string_schema(), "timeout": number_schema()}),
    )
    def _resolve_pair(params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = context_from_params(params)
        pairs = params.get("pairs") or list(DEFAULT_PREFERRED_TRANSFORMATION_PAIRS)
        pair = ctx.client().resolve_preferred_transformation_pair([tuple(item) for item in pairs])
        return {"add": pair.add, "subtract": pair.subtract}

    @registry.tool(
        namespace="core",
        name="ensure_preflight",
        description="Authenticate, ensure required connectors exist, and resolve a preferred transformation pair.",
        input_schema=object_schema(
            {
                "required_connectors": array_schema(),
                "preferred_transformation_pairs": array_schema(),
                "private_key": string_schema(),
                "api_base": string_schema(),
                "timeout": number_schema(),
            },
            required=["required_connectors"],
        ),
    )
    def _ensure_preflight(params: Dict[str, Any]) -> Dict[str, Any]:
        ctx = context_from_params(params)
        acct = ctx.account()
        pair = ctx.client().ensure_preflight(
            acct,
            required_connectors=list(params["required_connectors"]),
            preferred_transformation_pairs=[tuple(item) for item in (params.get("preferred_transformation_pairs") or list(DEFAULT_PREFERRED_TRANSFORMATION_PAIRS))],
        )
        return {"add": pair.add, "subtract": pair.subtract, "address": acct.address}

    @registry.tool(
        namespace="core",
        name="build_parent_connector",
        description="Build a generic structural parent connector over child connector names.",
        input_schema=object_schema({"name": string_schema(), "child_names": array_schema(string_schema())}, required=["name", "child_names"]),
    )
    def _build_parent(params: Dict[str, Any]) -> Dict[str, Any]:
        return build_parent_connector(params["child_names"], name=params["name"])
