import unittest

from decentralised_art_mcp.resources import resource_uri
from decentralised_art_mcp.server import build_registries


class ResourceTests(unittest.TestCase):
    def test_can_read_registered_resource(self):
        _, resources = build_registries()
        resource = resources.read("core.primer")
        self.assertEqual(resource["mime_type"], "text/markdown")
        self.assertIn("format-agnostic", resource["text"])
        self.assertEqual(resource["uri"], resource_uri("core.primer"))

    def test_only_core_resource_is_registered(self):
        _, resources = build_registries()
        self.assertEqual([item["name"] for item in resources.describe_resources()], ["core.primer"])


if __name__ == "__main__":
    unittest.main()
