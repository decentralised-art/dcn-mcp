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

    def test_can_read_score_template_workflow_resource(self):
        _, _, resources = build_registries()
        resource = resources.read("music.score_templates_workflow")
        self.assertEqual(resource["mime_type"], "text/markdown")
        self.assertIn("local editable draft arrangements", resource["text"])
        self.assertIn("score_full_v2", resource["text"])
        self.assertIn("score_meter_v2", resource["text"])
        self.assertIn("score_notes_v1", resource["text"])
        self.assertIn("score_onset", resource["text"])
        self.assertIn("score_duration", resource["text"])
        self.assertIn("trees within trees", resource["text"])
        self.assertIn("add` transformation with argument `1", resource["text"])
        self.assertEqual(resource["uri"], resource_uri("music.score_templates_workflow"))


if __name__ == "__main__":
    unittest.main()
