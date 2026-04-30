from __future__ import annotations

import json
import math
import pathlib
import subprocess
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..inspect import coerce_number_stream, strip_index_suffix
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
DEFAULT_MIDI_EXPORT_TIMEOUT_SECONDS = 30.0


def parse_role(path: str) -> Optional[str]:
    trimmed = str(path or "").strip()
    if not trimmed:
        return None
    tail = trimmed.split("/")[-1].strip().lower()
    tail = strip_index_suffix(tail)
    return ROLE_ALIASES.get(tail)


def _group_note_stream_records_with_diagnostics(samples: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Dict[str, Any]]], List[str], Dict[str, int]]:
    grouped: Dict[str, Dict[str, Dict[str, Any]]] = {}
    unknown_paths: List[str] = []
    diagnostics = {
        "duplicate_stream_count": 0,
        "invalid_value_count": 0,
        "skipped_note_count": 0,
    }
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
        group_key = "/" + "/".join(segments[:-1]) if len(segments) > 1 else "/root"
        values, invalid_count = coerce_number_stream(sample.get("data"))
        diagnostics["invalid_value_count"] += invalid_count
        streams = grouped.setdefault(group_key, {})
        if role in streams:
            diagnostics["duplicate_stream_count"] += 1
            streams[role]["values"].extend(values)
            streams[role]["paths"].append(path)
        else:
            streams[role] = {"values": values, "paths": [path]}
    return grouped, unknown_paths, diagnostics


def group_note_streams_with_diagnostics(samples: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, List[float]]], List[str], Dict[str, int]]:
    records, unknown_paths, diagnostics = _group_note_stream_records_with_diagnostics(samples)
    grouped = {
        group_key: {role: list(record["values"]) for role, record in streams.items()}
        for group_key, streams in records.items()
    }
    return grouped, unknown_paths, diagnostics


def group_note_streams(samples: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, List[float]]], List[str]]:
    grouped, unknown_paths, _diagnostics = group_note_streams_with_diagnostics(samples)
    return grouped, unknown_paths


def collect_note_events_with_diagnostics(samples: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str], List[str], Dict[str, int]]:
    grouped, unknown_paths, diagnostics = _group_note_stream_records_with_diagnostics(samples)
    events: List[Dict[str, Any]] = []
    usable_groups: List[str] = []
    for group_key, streams in grouped.items():
        if any(role not in streams for role in REQUIRED_ROLES):
            continue
        usable_groups.append(group_key)
        pitch = list(streams["pitch"]["values"])
        time_stream = list(streams["time"]["values"])
        duration = list(streams["duration"]["values"])
        velocity = list(streams["velocity"]["values"])
        count = min(len(pitch), len(time_stream), len(duration), len(velocity))
        for index in range(count):
            pitch_value = float(pitch[index])
            time_value = float(time_stream[index])
            duration_value = float(duration[index])
            velocity_value = float(velocity[index])
            if pitch_value < 0 or pitch_value > 127 or time_value < 0 or duration_value <= 0 or velocity_value < 0 or velocity_value > 127:
                diagnostics["skipped_note_count"] += 1
                continue
            events.append(
                {
                    "group": group_key,
                    "pitch": int(round(pitch_value)),
                    "time": _clean_number(time_value),
                    "duration": _clean_number(duration_value),
                    "velocity": int(round(velocity_value)),
                    "source_paths": sorted(
                        {
                            *streams["pitch"]["paths"],
                            *streams["time"]["paths"],
                            *streams["duration"]["paths"],
                            *streams["velocity"]["paths"],
                        }
                    ),
                }
            )
    return events, unknown_paths, usable_groups, diagnostics


def collect_note_events(samples: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    events, unknown_paths, usable_groups, _diagnostics = collect_note_events_with_diagnostics(samples)
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
    gaps = [max(0.0, float(ordered[index]["time"]) - float(ordered[index - 1]["time"])) for index in range(1, len(ordered))]
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
    ordered = sorted(events, key=lambda item: (_float_value(item.get("time")), _float_value(item.get("pitch")), _float_value(item.get("velocity"))))
    return [
        {"path": "/composition/pitch", "data": [_midi_value(item.get("pitch")) for item in ordered]},
        {"path": "/composition/time", "data": [_clean_number(max(0.0, _float_value(item.get("time")))) for item in ordered]},
        {"path": "/composition/duration", "data": [_clean_number(max(0.0, _float_value(item.get("duration")))) for item in ordered]},
        {"path": "/composition/velocity", "data": [_midi_value(item.get("velocity")) for item in ordered]},
    ]


def _float_value(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return number if math.isfinite(number) else default


def _midi_value(value: Any) -> int:
    return max(0, min(127, int(round(_float_value(value)))))


def _clean_number(value: float) -> Any:
    return int(value) if float(value).is_integer() else value


def export_midi(input_json: pathlib.Path, output_mid: pathlib.Path, *, timeout: float = DEFAULT_MIDI_EXPORT_TIMEOUT_SECONDS) -> Dict[str, Any]:
    script_path = pathlib.Path(__file__).resolve().parent.parent / "assets" / "pt2midi.js"
    result = subprocess.run(
        ["node", str(script_path), str(input_json), str(output_mid)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=float(timeout),
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
        normalized = {
            ROLE_ALIASES.get(strip_index_suffix(str(item).strip().lower()), str(item).strip().lower())
            for item in leaves
        }
        return set(REQUIRED_ROLES).issubset(normalized)

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
            events, unknown_paths, usable_groups, diagnostics = collect_note_events_with_diagnostics(list(params["samples"]))
            return {"events": events, "unknown_paths": unknown_paths, "usable_groups": usable_groups, "diagnostics": diagnostics}

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
