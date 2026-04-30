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
    if isinstance(exc, DCNMCPError):
        return exc.to_payload()
    return InternalToolError(
        "Internal tool error.",
        details={"exception_type": exc.__class__.__name__},
    ).to_payload()
