from __future__ import annotations

import json
import pathlib
import subprocess
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..inspect import strip_index_suffix
from ..registry import ToolRegistry
from ..resources import ResourceRegistry
from ..schemas import array_schema, integer_schema, object_schema, string_schema
from .base import FormatAdapter

ROLE_ALIASES: Dict[str, str] = {
    "time": "time",
    "duration": "duration",
    "durationv2": "duration",
    "duration_v2": "duration",
    "pitch": "pitch",
    "velocity": "velocity",
}
REQUIRED_ROLES: Tuple[str, ...] = ("pitch", "time", "duration", "velocity")
BASE_CONNECTORS: Dict[str, str] = {
    "time": "time",
    "duration": "duration",
    "pitch": "pitch",
    "velocity": "velocity",
}


def _coerce_int_list(value: Any) -> List[int]:
    if not isinstance(value, list):
        return []
    out: List[int] = []
    for item in value:
        try:
            out.append(int(item))
        except Exception:
            continue
    return out


def parse_role(path: str) -> Optional[str]:
    trimmed = str(path or "").strip()
    if not trimmed:
        return None
    tail = trimmed.split("/")[-1].strip().lower()
    tail = strip_index_suffix(tail)
    return ROLE_ALIASES.get(tail)


def group_note_streams(samples: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, List[int]]], List[str]]:
    grouped: Dict[str, Dict[str, List[int]]] = {}
    unknown_paths: List[str] = []
    for sample in samples:
        path = str(sample.get("path") or sample.get("feature_path") or "").strip()
        if not path:
            unknown_paths.append("<missing path>")
            continue
        role = parse_role(path)
        if role is None:
            unknown_paths.append(path)
            continue
        segments = [segment for segment in path.split("/") if segment]
        group_key = "/" + "/".join(strip_index_suffix(segment) for segment in segments[:-1]) if len(segments) > 1 else "/root"
        grouped.setdefault(group_key, {})[role] = _coerce_int_list(sample.get("data"))
    return grouped, unknown_paths


def collect_note_events(samples: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    grouped, unknown_paths = group_note_streams(samples)
    events: List[Dict[str, Any]] = []
    usable_groups: List[str] = []
    for group_key, streams in grouped.items():
        if any(role not in streams for role in REQUIRED_ROLES):
            continue
        usable_groups.append(group_key)
        pitch = list(streams["pitch"])
        time_stream = list(streams["time"])
        duration = list(streams["duration"])
        velocity = list(streams["velocity"])
        count = min(len(pitch), len(time_stream), len(duration), len(velocity))
        for index in range(count):
            if int(duration[index]) <= 0 or int(velocity[index]) <= 0:
                continue
            events.append(
                {
                    "group": group_key,
                    "pitch": int(pitch[index]),
                    "time": int(time_stream[index]),
                    "duration": int(duration[index]),
                    "velocity": int(velocity[index]),
                }
            )
    return events, unknown_paths, usable_groups


def summarize_note_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not events:
        return {
            "event_count": 0,
            "time_min": 0,
            "time_max": 0,
            "time_span": 0,
            "pitch_min": 0,
            "pitch_max": 0,
            "pitch_median": 0,
            "duration_min": 0,
            "duration_max": 0,
            "velocity_min": 0,
            "velocity_max": 0,
            "avg_gap": 0.0,
            "events": [],
        }
    ordered = sorted(events, key=lambda item: (item["time"], item["pitch"]))
    gaps = [max(0, int(ordered[index]["time"]) - int(ordered[index - 1]["time"])) for index in range(1, len(ordered))]
    pitches = sorted(item["pitch"] for item in ordered)
    return {
        "event_count": len(ordered),
        "time_min": min(item["time"] for item in ordered),
        "time_max": max(item["time"] for item in ordered),
        "time_span": max(item["time"] for item in ordered) - min(item["time"] for item in ordered),
        "pitch_min": min(pitches),
        "pitch_max": max(pitches),
        "pitch_median": pitches[len(pitches) // 2],
        "duration_min": min(item["duration"] for item in ordered),
        "duration_max": max(item["duration"] for item in ordered),
        "velocity_min": min(item["velocity"] for item in ordered),
        "velocity_max": max(item["velocity"] for item in ordered),
        "avg_gap": (sum(gaps) / len(gaps)) if gaps else 0.0,
        "events": ordered[:16],
    }


def classify_register(summary: Dict[str, Any]) -> Dict[str, Any]:
    if not summary.get("event_count"):
        return {"label": "empty", "range": [0, 0]}
    lo = int(summary["pitch_min"])
    hi = int(summary["pitch_max"])
    median = int(summary.get("pitch_median", lo))
    if hi <= 35:
        label = "sub-bass"
    elif median <= 52:
        label = "bass"
    elif median <= 60:
        label = "low-mid"
    elif median <= 72:
        label = "mid"
    else:
        label = "upper"
    return {"label": label, "range": [lo, hi], "median": median}


def build_wrapper_connector(base_connector: Dict[str, Any], *, wrapper_name: str, start_time: int, static_ri: Dict[str, Dict[str, int]], add_transformation: str) -> Dict[str, Any]:
    payload = json.loads(json.dumps(base_connector))
    payload["name"] = str(wrapper_name)
    if int(start_time) > 0:
        for dimension in payload.get("dimensions", []):
            if dimension.get("composite") == BASE_CONNECTORS["time"]:
                dimension["transformations"] = [{"name": add_transformation, "args": [int(start_time)]}, *list(dimension.get("transformations") or [])]
                break
    payload["static_ri"] = {**dict(payload.get("static_ri") or {}), **dict(static_ri or {})}
    return payload


def build_player_payload(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ordered = sorted(events, key=lambda item: (item["time"], item["pitch"], item["velocity"]))
    return [
        {"path": "/composition/pitch", "data": [max(0, min(127, int(item["pitch"]))) for item in ordered]},
        {"path": "/composition/time", "data": [max(0, int(item["time"])) for item in ordered]},
        {"path": "/composition/duration", "data": [max(1, min(127, int(item["duration"]))) for item in ordered]},
        {"path": "/composition/velocity", "data": [max(1, min(127, int(item["velocity"]))) for item in ordered]},
    ]


def export_midi(input_json: pathlib.Path, output_mid: pathlib.Path) -> Dict[str, Any]:
    script_path = pathlib.Path(__file__).resolve().parent.parent / "assets" / "pt2midi.js"
    result = subprocess.run(
        ["node", str(script_path), str(input_json), str(output_mid)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return {
        "script": str(script_path),
        "input_json": str(input_json),
        "output_mid": str(output_mid),
        "stdout": result.stdout.strip(),
    }


class PTDVMusicAdapter(FormatAdapter):
    name = "ptdv_music"
    description = "PTDV/music specialist adapter for note-event extraction, register analysis, wrapper construction, and MIDI export."

    def supports_leaves(self, leaves: Iterable[str]) -> bool:
        return set(REQUIRED_ROLES).issubset({str(item).lower() for item in leaves})

    def register_resources(self, registry: ResourceRegistry) -> None:
        base = pathlib.Path(__file__).resolve().parent.parent / "resources" / "music"
        registry.register_markdown(
            name="music.ptdv_music_workflow",
            description="PTDV/music workflow guidance for vocabulary, wrappers, sections, and final collection.",
            path=base / "ptdv_music_workflow.md",
        )
        registry.register_markdown(
            name="music.register_maps",
            description="Practical PTDV/music register maps for piano-oriented pitch ranges.",
            path=base / "register_maps.md",
        )

    def register_tools(self, registry: ToolRegistry) -> None:
        @registry.tool(
            namespace="music",
            name="extract_note_events",
            description="Extract PTDV note events from execution samples.",
            input_schema=object_schema({"samples": array_schema()}, required=["samples"]),
        )
        def _extract(params: Dict[str, Any]) -> Dict[str, Any]:
            events, unknown_paths, usable_groups = collect_note_events(list(params["samples"]))
            return {"events": events, "unknown_paths": unknown_paths, "usable_groups": usable_groups}

        @registry.tool(
            namespace="music",
            name="summarize_note_events",
            description="Summarize PTDV note events and classify realized register.",
            input_schema=object_schema({"events": array_schema()}, required=["events"]),
        )
        def _summarize(params: Dict[str, Any]) -> Dict[str, Any]:
            summary = summarize_note_events(list(params["events"]))
            return {"summary": summary, "register": classify_register(summary)}

        @registry.tool(
            namespace="music",
            name="build_wrapper_connector",
            description="Build a PTDV/music wrapper connector over an existing base connector using start_time and static_ri.",
            input_schema=object_schema(
                {
                    "base_connector": object_schema(),
                    "wrapper_name": string_schema(),
                    "start_time": integer_schema(),
                    "static_ri": object_schema(),
                    "add_transformation": string_schema(),
                },
                required=["base_connector", "wrapper_name", "start_time", "static_ri", "add_transformation"],
            ),
        )
        def _build_wrapper(params: Dict[str, Any]) -> Dict[str, Any]:
            return build_wrapper_connector(
                params["base_connector"],
                wrapper_name=params["wrapper_name"],
                start_time=int(params["start_time"]),
                static_ri=dict(params["static_ri"]),
                add_transformation=str(params["add_transformation"]),
            )

        @registry.tool(
            namespace="music",
            name="build_player_payload",
            description="Build a flat PTDV player payload from note events for MIDI export.",
            input_schema=object_schema({"events": array_schema()}, required=["events"]),
        )
        def _build_payload(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"payload": build_player_payload(list(params["events"]))}
