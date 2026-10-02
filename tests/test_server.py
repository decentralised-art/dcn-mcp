import unittest

from decentralised_art_mcp.server import build_registries


class ServerTests(unittest.TestCase):
    def test_server_exposes_only_core_tools_and_resources(self):
        registry, resources = build_registries()
        tool_names = {item["full_name"] for item in registry.describe_tools()}
        self.assertTrue(tool_names)
        self.assertTrue(all(name.startswith("core.") for name in tool_names))
        self.assertIn("core.connector_exists", tool_names)
        self.assertIn("core.build_parent_connector", tool_names)
        self.assertIn("core.transformation_exists", tool_names)
        self.assertIn("core.condition_exists", tool_names)
        self.assertIn("core.get_account", tool_names)
        self.assertIn("core.get_feed_page", tool_names)
        self.assertIn("core.get_feed_stream_replay", tool_names)
        self.assertIn("core.get_nonce", tool_names)
        for name in (
            "create_connector", "create_transformation", "create_condition",
            "simulate_connector", "prepare_publication", "publish_entity",
            "confirm_publication", "execute_connector",
        ):
            self.assertIn(f"core.{name}", tool_names)
        for kind in ("connector", "transformation", "condition"):
            self.assertNotIn(f"core.deploy_{kind}", tool_names)
        resource_names = {item["name"] for item in resources.describe_resources()}
        self.assertEqual(resource_names, {"core.primer"})


if __name__ == "__main__":
    unittest.main()
