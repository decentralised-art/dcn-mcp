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

    def test_can_read_score_position_schema_workflow_resource(self):
        _, _, resources = build_registries()
        resource = resources.read("music.score_position_schema_workflow")
        self.assertEqual(resource["mime_type"], "text/markdown")
        self.assertIn("Music Score plugin uses a positional score schema", resource["text"])
        self.assertIn("D1 Notes", resource["text"])
        self.assertIn("D1 `onset_tick`", resource["text"])
        self.assertIn("D2 `duration_tick`", resource["text"])
        self.assertIn("D3 `pitch`", resource["text"])
        self.assertIn("score_quarter_note_tick_grid", resource["text"])
        self.assertIn("constant_value", resource["text"])
        self.assertIn("major_scale_steps", resource["text"])
        self.assertIn("2520` ticks per quarter note", resource["text"])
        self.assertIn("Existing on-chain connectors should remain references", resource["text"])
        self.assertIn("A binding is not an edit to the reused connector", resource["text"])
        self.assertIn("root connector's `static_ri`", resource["text"])
        self.assertIn("Do not say \"insert a template\"", resource["text"])
        self.assertNotIn("score_full_v3", resource["text"])
        self.assertNotIn("score_notes_v2", resource["text"])
        self.assertEqual(resource["uri"], resource_uri("music.score_position_schema_workflow"))


if __name__ == "__main__":
    unittest.main()
