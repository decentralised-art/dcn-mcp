from __future__ import annotations

from typing import Any, Dict, Optional


class DCNMCPError(Exception):
    code = "dcn_mcp_error"

    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = str(message)
        self.details = details or {}

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class ValidationError(DCNMCPError):
    code = "validation_error"


class ToolNotFoundError(DCNMCPError):
    code = "tool_not_found"


class ResourceNotFoundError(DCNMCPError):
    code = "resource_not_found"


class AuthConfigurationError(DCNMCPError):
    code = "auth_configuration_error"


class InternalToolError(DCNMCPError):
    code = "internal_tool_error"


def error_to_payload(exc: Exception) -> Dict[str, Any]:
    import requests
    from .lifecycle import PublicationPending
    if isinstance(exc, PublicationPending):
        return {"code": "publication_pending", "message": str(exc), "details": exc.publication}
    if isinstance(exc, ValueError):
        return {"code": "validation_error", "message": str(exc)}
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        try:
            body = exc.response.json()
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}
        details = {"status_code": exc.response.status_code}
        for key in ("missing", "mismatched"):
            if isinstance(body.get(key), list):
                details[key] = body[key]
        return {"code": "http_error", "message": str(body.get("message") or "decentralised.art request failed"), "details": details}
    if isinstance(exc, DCNMCPError):
        return exc.to_payload()
    return InternalToolError(
        "Internal tool error.",
        details={"exception_type": exc.__class__.__name__},
    ).to_payload()
