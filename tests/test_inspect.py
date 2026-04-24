import unittest

from dcn_mcp.inspect import group_samples_by_parent, summarize_samples


SAMPLES = [
    {"path": "/foo:0/pitch:0", "data": [1, 2]},
    {"path": "/foo:0/time:0", "data": [3, 4]},
    {"path": "/foo:1/pitch:0", "data": [5]},
]


class InspectTests(unittest.TestCase):
    def test_group_samples_by_parent_normalizes_indices(self):
        grouped, unknown = group_samples_by_parent(SAMPLES)
        self.assertEqual(unknown, [])
        self.assertIn("/foo", grouped)
        self.assertEqual(grouped["/foo"]["pitch"], [1, 2, 5])
        self.assertEqual(grouped["/foo"]["time"], [3, 4])

    def test_summarize_samples_reports_leafs(self):
        summary = summarize_samples(SAMPLES)
        self.assertEqual(summary["group_count"], 1)
        self.assertEqual(set(summary["leaf_names"]), {"pitch", "time"})
        self.assertEqual(summary["duplicate_stream_count"], 1)

    def test_summarize_samples_counts_invalid_values(self):
        summary = summarize_samples([{"path": "/foo/pitch", "data": [1, "bad", None]}])
        self.assertEqual(summary["invalid_value_count"], 2)
        self.assertEqual(summary["max_stream_length"], 1)


if __name__ == "__main__":
    unittest.main()
