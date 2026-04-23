import unittest

from dcn_mcp.adapters.ptdv_music import (
    build_player_payload,
    build_wrapper_connector,
    classify_register,
    collect_note_events,
    summarize_note_events,
)
from dcn_mcp.tools.core import build_parent_connector


SAMPLES = [
    {"path": "/cell:0/pitch:0", "data": [48, 52]},
    {"path": "/cell:0/time:0", "data": [0, 4]},
    {"path": "/cell:0/duration:0", "data": [2, 2]},
    {"path": "/cell:0/velocity:0", "data": [80, 90]},
]


class PTDVMusicTests(unittest.TestCase):
    def test_collect_and_summarize_note_events(self):
        events, unknown, groups = collect_note_events(SAMPLES)
        self.assertEqual(unknown, [])
        self.assertEqual(groups, ["/cell"])
        summary = summarize_note_events(events)
        self.assertEqual(summary["event_count"], 2)
        self.assertEqual(summary["pitch_min"], 48)
        self.assertEqual(classify_register(summary)["label"], "bass")

    def test_build_wrapper_connector_adds_time_transform_and_static_ri(self):
        base = {
            "name": "base",
            "dimensions": [
                {"composite": "time", "transformations": [{"name": "math_add_v1", "args": [1]}], "bindings": {}},
                {"composite": "duration", "transformations": [], "bindings": {}},
                {"composite": "pitch", "transformations": [], "bindings": {}},
                {"composite": "velocity", "transformations": [], "bindings": {}},
            ],
            "static_ri": {},
        }
        wrapped = build_wrapper_connector(base, wrapper_name="wrap", start_time=6, static_ri={"3": {"start_point": 60, "transformation_shift": 0}}, add_transformation="math_add_v1")
        self.assertEqual(wrapped["dimensions"][0]["transformations"][0], {"name": "math_add_v1", "args": [6]})
        self.assertEqual(wrapped["static_ri"]["3"]["start_point"], 60)

    def test_build_parent_and_payload(self):
        parent = build_parent_connector(["a", "b"], name="piece")
        self.assertEqual(len(parent["dimensions"]), 2)
        payload = build_player_payload([
            {"pitch": 140, "time": -1, "duration": 0, "velocity": 200},
            {"pitch": 60, "time": 4, "duration": 3, "velocity": 100},
        ])
        self.assertEqual(payload[0]["data"], [127, 60])
        self.assertEqual(payload[1]["data"], [0, 4])
        self.assertEqual(payload[2]["data"], [1, 3])
        self.assertEqual(payload[3]["data"], [127, 100])


if __name__ == "__main__":
    unittest.main()
