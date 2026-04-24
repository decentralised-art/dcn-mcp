from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import quote

import requests
from eth_account.messages import encode_defunct

from .models import ChainCursor, TransformationPair


class DCNClient:
    def __init__(self, base_url: str, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = float(timeout)
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self.access_token: Optional[str] = None

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "DCNClient":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def _handle_response(self, response: requests.Response) -> Any:
        try:
            data = response.json()
        except json.JSONDecodeError:
            response.raise_for_status()
            return {"raw": response.text}
        if not response.ok:
            raise requests.HTTPError(f"{response.status_code} {data}", response=response)
        return data

    def _authz_headers(self) -> Dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    def _get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        return self.session.get(
            f"{self.base_url}{path}",
            params=params,
            headers=self._authz_headers(),
            timeout=self.timeout,
        )

    def _post_with_reauth(self, path: str, payload: Dict[str, Any], acct) -> requests.Response:
        self.ensure_auth(acct)
        url = f"{self.base_url}{path}"
        response = self.session.post(
            url,
            json=payload,
            headers=self._authz_headers(),
            timeout=self.timeout,
        )
        if response.status_code == 401:
            self.access_token = None
            self.ensure_auth(acct)
            response = self.session.post(
                url,
                json=payload,
                headers=self._authz_headers(),
                timeout=self.timeout,
            )
        return response

    def get_nonce(self, address: str) -> str:
        response = self.session.get(f"{self.base_url}/nonce/{_path_segment(address)}", timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and "nonce" in payload:
            return str(payload["nonce"])
        raise ValueError(f"Unexpected nonce response shape: {payload}")

    def post_auth(self, address: str, message: str, signature: str) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/auth",
            json={"address": address, "message": message, "signature": signature},
            timeout=self.timeout,
        )
        data = self._handle_response(response)
        self.access_token = data.get("access_token")
        return data

    def ensure_auth(self, acct) -> None:
        if self.access_token:
            return
        nonce = self.get_nonce(acct.address)
        message = f"Login nonce: {nonce}"
        signature = acct.sign_message(encode_defunct(text=message)).signature.hex()
        auth_result = self.post_auth(acct.address, message, signature)
        if not self.access_token:
            raise RuntimeError(f"Auth failed — missing access token: {auth_result}")

    def get_connector(self, name: str) -> Dict[str, Any]:
        return self._handle_response(self._get(f"/connector/{_path_segment(name)}"))

    def get_transformation(self, name: str) -> Dict[str, Any]:
        return self._handle_response(self._get(f"/transformation/{_path_segment(name)}"))

    def connector_exists(self, name: str) -> bool:
        response = self._get(f"/connector/{_path_segment(name)}")
        if response.status_code == 404:
            return False
        if response.ok:
            return True
        body = (response.text or "").strip().replace("\n", " ")
        raise RuntimeError(f"Failed to check connector '{name}': {response.status_code} {body}")

    def transformation_exists(self, name: str) -> bool:
        response = self._get(f"/transformation/{_path_segment(name)}")
        if response.status_code == 404:
            return False
        if response.ok:
            return True
        body = (response.text or "").strip().replace("\n", " ")
        raise RuntimeError(f"Failed to check transformation '{name}': {response.status_code} {body}")

    def post_connector(self, payload: Dict[str, Any], acct) -> Dict[str, Any]:
        return self._handle_response(self._post_with_reauth("/connector", payload, acct))

    def execute_connector(
        self,
        acct,
        connector_name: str,
        particles_count: int,
        dynamic_ri: Optional[Dict[str, Dict[str, int]]] = None,
    ) -> List[Dict[str, Any]]:
        payload = {
            "connector_name": connector_name,
            "particles_count": int(particles_count),
            "dynamic_ri": dynamic_ri or {},
        }
        data = self._handle_response(self._post_with_reauth("/execute", payload, acct))
        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected /execute response shape: {type(data).__name__}")
        return data

    def list_formats(self, limit: int = 100, after: Optional[str] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": int(limit)}
        if after is not None:
            params["after"] = after
        return self._handle_response(self._get("/formats", params=params))

    def get_format(self, format_hash: str, limit: int = 256, after: Optional[str] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": int(limit)}
        if after is not None:
            params["after"] = after
        return self._handle_response(self._get(f"/format/{_path_segment(format_hash)}", params=params))

    def get_account(
        self,
        address: str,
        *,
        limit: int = 256,
        after_connectors: Optional[str] = None,
        after_transformations: Optional[str] = None,
        after_conditions: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": int(limit)}
        if after_connectors is not None:
            params["after_connectors"] = after_connectors
        if after_transformations is not None:
            params["after_transformations"] = after_transformations
        if after_conditions is not None:
            params["after_conditions"] = after_conditions
        return self._handle_response(self._get(f"/account/{_path_segment(address)}", params=params))

    def ensure_connectors_exist(self, names: Iterable[str]) -> None:
        missing = [name for name in names if not self.connector_exists(name)]
        if missing:
            raise RuntimeError("Missing required connector primitives: " + ", ".join(missing))

    def resolve_preferred_transformation_pair(self, preferred_pairs: Sequence[Tuple[str, str]]) -> TransformationPair:
        for add_name, subtract_name in preferred_pairs:
            if self.transformation_exists(add_name) and self.transformation_exists(subtract_name):
                return TransformationPair(add=add_name, subtract=subtract_name)
        attempted = [f"{add}/{subtract}" for add, subtract in preferred_pairs]
        raise RuntimeError("No supported transformation pair found on the network. Tried: " + ", ".join(attempted))

    def ensure_preflight(self, acct, *, required_connectors: Sequence[str], preferred_transformation_pairs: Sequence[Tuple[str, str]]) -> TransformationPair:
        self.ensure_auth(acct)
        self.ensure_connectors_exist(required_connectors)
        return self.resolve_preferred_transformation_pair(preferred_transformation_pairs)


def resolve_cursor(payload: Dict[str, Any]) -> ChainCursor:
    cursor = payload.get("cursor")
    if isinstance(cursor, dict):
        return ChainCursor(
            has_more=bool(cursor.get("has_more")),
            next_after=(str(cursor.get("next_after")).strip() if cursor.get("next_after") else None),
        )
    return ChainCursor(
        has_more=bool(payload.get("has_more")),
        next_after=(str(payload.get("next_after")).strip() if payload.get("next_after") else None),
    )


def _path_segment(value: object) -> str:
    return quote(str(value).strip(), safe="")
