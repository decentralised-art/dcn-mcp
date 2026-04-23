from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from .auth import load_account
from .client import DCNClient
from .config import DEFAULT_API_BASE, DEFAULT_TIMEOUT
from .errors import AuthConfigurationError

ClientFactory = Callable[[str, float], Any]
AccountLoader = Callable[[Optional[str]], Any]

_CLIENT_FACTORY_OVERRIDE: Optional[ClientFactory] = None
_ACCOUNT_LOADER_OVERRIDE: Optional[AccountLoader] = None


def set_runtime_overrides(*, client_factory: Optional[ClientFactory] = None, account_loader: Optional[AccountLoader] = None) -> None:
    global _CLIENT_FACTORY_OVERRIDE, _ACCOUNT_LOADER_OVERRIDE
    _CLIENT_FACTORY_OVERRIDE = client_factory
    _ACCOUNT_LOADER_OVERRIDE = account_loader


def clear_runtime_overrides() -> None:
    set_runtime_overrides(client_factory=None, account_loader=None)


@dataclass
class RuntimeContext:
    api_base: str = DEFAULT_API_BASE
    timeout: float = DEFAULT_TIMEOUT
    private_key: Optional[str] = None
    client_factory: Optional[ClientFactory] = None
    account_loader: Optional[AccountLoader] = None
    _client: Optional[Any] = field(default=None, init=False, repr=False)
    _account: Any = field(default=None, init=False, repr=False)

    def client(self) -> Any:
        if self._client is None:
            factory = self.client_factory or _CLIENT_FACTORY_OVERRIDE or (lambda api_base, timeout: DCNClient(api_base, timeout=timeout))
            self._client = factory(str(self.api_base), float(self.timeout))
        return self._client

    def account(self, *, required: bool = True):
        if self._account is not None:
            return self._account
        loader = self.account_loader or _ACCOUNT_LOADER_OVERRIDE or load_account
        try:
            self._account = loader(self.private_key)
            return self._account
        except Exception as exc:
            if not required:
                return None
            raise AuthConfigurationError(
                "Missing or invalid account configuration.",
                details={"reason": str(exc)},
            ) from exc


def context_from_params(params: Dict[str, Any]) -> RuntimeContext:
    return RuntimeContext(
        api_base=str(params.get("api_base") or DEFAULT_API_BASE),
        timeout=float(params.get("timeout") or DEFAULT_TIMEOUT),
        private_key=params.get("private_key"),
    )
