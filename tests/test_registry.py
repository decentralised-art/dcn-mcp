import unittest

from decentralised_art_mcp.registry import ToolRegistry
from decentralised_art_mcp.schemas import integer_schema, object_schema


class RegistryTests(unittest.TestCase):
    def test_registry_register_and_invoke(self):
        registry = ToolRegistry()

        @registry.tool(namespace="test", name="echo", description="echo", input_schema=object_schema({"a": integer_schema()}, required=["a"]))
        def _echo(params):
            return {"payload": params}

        result = registry.invoke("test.echo", {"a": 1})
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"], {"payload": {"a": 1}})
        described = registry.describe_tools()
        self.assertEqual(described[0]["full_name"], "test.echo")

    def test_registry_returns_validation_error_envelope(self):
        registry = ToolRegistry()

        @registry.tool(namespace="test", name="echo", description="echo", input_schema=object_schema({"a": integer_schema()}, required=["a"]))
        def _echo(params):
            return {"payload": params}

        result = registry.invoke("test.echo", {"a": "bad"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "validation_error")

    def test_registry_does_not_expose_raw_internal_exception_messages(self):
        registry = ToolRegistry()

        @registry.tool(namespace="test", name="boom", description="boom", input_schema=object_schema())
        def _boom(_params):
            raise RuntimeError("secret-token /tmp/private")

        result = registry.invoke("test.boom", {})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "internal_tool_error")
        self.assertEqual(result["error"]["message"], "Internal tool error.")
        self.assertNotIn("secret-token", str(result["error"]))


if __name__ == "__main__":
    unittest.main()
