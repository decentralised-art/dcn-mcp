import unittest

from dcn_mcp.context import clear_runtime_overrides, set_runtime_overrides
from dcn_mcp.server import build_registries


class FakeAccount:
    address = "0xabc"


class FakeClient:
    def __init__(self, api_base, timeout):
        self.api_base = api_base
        self.timeout = timeout

    def connector_exists(self, name):
        return name == "pitch"

    def transformation_exists(self, name):
        return name == "math_add_v1"

    def get_connector(self, name):
        return {"name": name, "dimensions": []}

    def get_transformation(self, name):
        return {"name": name, "code": "// solidity"}

    def list_formats(self, limit=100, after=None):
        return {"formats": ["fmt1"], "limit": limit, "after": after}

    def get_format(self, format_hash, limit=256, after=None):
        return {"format_hash": format_hash, "features": ["pitch", "time"], "limit": limit, "after": after}

    def get_account(self, address, *, limit=256, after_connectors=None, after_transformations=None, after_conditions=None):
        return {
            "address": address,
            "limit": limit,
            "owned_connectors": ["a", "b"],
            "owned_transformations": ["math_add_v1"],
            "owned_conditions": [],
            "cursor_connectors": {"has_more": False, "next_after": None},
            "cursor_transformations": {"has_more": False, "next_after": None},
            "cursor_conditions": {"has_more": False, "next_after": None},
        }

    def ensure_preflight(self, acct, *, required_connectors, preferred_transformation_pairs):
        class Pair:
            add = "math_add_v1"
            subtract = "math_subtract_v1"
        return Pair()

    def post_connector(self, payload, acct):
        return {"name": payload.get("name"), "owner": acct.address}

    def execute_connector(self, acct, connector_name, particles_count, dynamic_ri=None):
        return [{"path": "/cell:0/pitch:0", "data": [60]}]


def fake_account_loader(_private_key):
    return FakeAccount()


class CoreIntegrationTests(unittest.TestCase):
    def setUp(self):
        set_runtime_overrides(client_factory=lambda api_base, timeout: FakeClient(api_base, timeout), account_loader=fake_account_loader)
        self.registry, _, _ = build_registries()

    def tearDown(self):
        clear_runtime_overrides()

    def test_connector_exists_uses_fake_client(self):
        result = self.registry.invoke("core.connector_exists", {"name": "pitch"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"], {"name": "pitch", "exists": True})

    def test_transformation_exists_uses_fake_client(self):
        result = self.registry.invoke("core.transformation_exists", {"name": "math_add_v1"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"], {"name": "math_add_v1", "exists": True})

    def test_get_account_uses_fake_client(self):
        result = self.registry.invoke("core.get_account", {"address": "0xabc", "limit": 64})
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["address"], "0xabc")
        self.assertEqual(result["data"]["limit"], 64)
        self.assertEqual(result["data"]["owned_connectors"], ["a", "b"])

    def test_execute_connector_uses_fake_client_and_account(self):
        result = self.registry.invoke("core.execute_connector", {"connector_name": "piece", "particles_count": 8})
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["samples"][0]["data"], [60])

    def test_ensure_preflight_uses_fake_client_and_account(self):
        result = self.registry.invoke("core.ensure_preflight", {"required_connectors": ["pitch", "time"]})
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["add"], "math_add_v1")
        self.assertEqual(result["data"]["address"], "0xabc")


if __name__ == "__main__":
    unittest.main()
