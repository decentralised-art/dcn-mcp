import unittest

from dcn_mcp.server import build_registries


class ServerTests(unittest.TestCase):
    def test_server_builds_core_and_music_tools_and_resources(self):
        registry, adapters, resources = build_registries()
        tool_names = {item["full_name"] for item in registry.describe_tools()}
        self.assertIn("core.connector_exists", tool_names)
        self.assertIn("core.build_parent_connector", tool_names)
        self.assertIn("core.transformation_exists", tool_names)
        self.assertIn("core.get_account", tool_names)
        self.assertIn("core.get_nonce", tool_names)
        self.assertIn("inspect.summarize_execution", tool_names)
        self.assertIn("music.extract_note_events", tool_names)
        self.assertNotIn("music.build_parent_connector", tool_names)
        adapter_names = {item["name"] for item in adapters.describe()}
        self.assertIn("ptdv_music", adapter_names)
        resource_names = {item["name"] for item in resources.describe_resources()}
        self.assertIn("core.dcn_core_primer", resource_names)
        self.assertIn("music.ptdv_music_workflow", resource_names)


if __name__ == "__main__":
    unittest.main()
