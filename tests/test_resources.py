import unittest

from dcn_mcp.resources import resource_uri
from dcn_mcp.server import build_registries


class ResourceTests(unittest.TestCase):
    def test_can_read_registered_resource(self):
        _, _, resources = build_registries()
        resource = resources.read("core.dcn_core_primer")
        self.assertEqual(resource["mime_type"], "text/markdown")
        self.assertIn("format-agnostic", resource["text"])
        self.assertEqual(resource["uri"], resource_uri("core.dcn_core_primer"))


if __name__ == "__main__":
    unittest.main()
