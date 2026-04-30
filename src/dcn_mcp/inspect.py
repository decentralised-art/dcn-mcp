from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


def sample_path(sample: Dict[str, Any]) -> str:
    return str(sample.get("path") or sample.get("feature_path") or "").strip()


def strip_index_suffix(segment: str) -> str:
    head, sep, tail = str(segment).rpartition(":")
    if sep and tail.isdigit():
        return head
    return str(segment)


def coerce_int_stream(value: Any) -> Tuple[List[int], int]:
    if not isinstance(value, list):
        return [], 1
    values: List[int] = []
    invalid_count = 0
    for item in value:
        try:
            values.append(int(item))
        except (TypeError, ValueError, OverflowError):
            invalid_count += 1
    return values, invalid_count


def coerce_number_stream(value: Any) -> Tuple[List[float], int]:
    if not isinstance(value, list):
        return [], 1
    values: List[float] = []
    invalid_count = 0
    for item in value:
        if isinstance(item, bool):
            invalid_count += 1
            continue
        try:
            number = float(item)
        except (TypeError, ValueError, OverflowError):
            invalid_count += 1
            continue
        if not math.isfinite(number):
            invalid_count += 1
            continue
        values.append(number)
    return values, invalid_count


def group_samples_by_parent_with_diagnostics(samples: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, List[int]]], List[str], Dict[str, int]]:
    grouped: Dict[str, Dict[str, List[int]]] = {}
    unknown_paths: List[str] = []
    diagnostics = {
        "duplicate_stream_count": 0,
        "invalid_value_count": 0,
    }
    for sample in samples:
        path = sample_path(sample)
        if not path:
            unknown_paths.append("<missing path>")
            continue
        segments = [segment for segment in path.split("/") if segment]
        if not segments:
            unknown_paths.append(path)
            continue
        leaf = strip_index_suffix(segments[-1]) or "unknown"
        group_key = "/" + "/".join(segments[:-1]) if len(segments) > 1 else "/root"
        values, invalid_count = coerce_int_stream(sample.get("data"))
        diagnostics["invalid_value_count"] += invalid_count
        streams = grouped.setdefault(group_key, {})
        if leaf in streams:
            diagnostics["duplicate_stream_count"] += 1
            streams[leaf].extend(values)
        else:
            streams[leaf] = values
    return grouped, unknown_paths, diagnostics


def group_samples_by_parent(samples: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, List[int]]], List[str]]:
    grouped, unknown_paths, _diagnostics = group_samples_by_parent_with_diagnostics(samples)
    return grouped, unknown_paths


def summarize_samples(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped, unknown_paths, diagnostics = group_samples_by_parent_with_diagnostics(samples)
    path_count = 0
    max_stream_length = 0
    leaves = set()
    for streams in grouped.values():
        path_count += len(streams)
        leaves.update(streams.keys())
        for values in streams.values():
            max_stream_length = max(max_stream_length, len(values))
    return {
        "sample_count": len(samples),
        "group_count": len(grouped),
        "path_count": path_count,
        "leaf_names": sorted(leaves),
        "unknown_path_count": len(unknown_paths),
        "unknown_paths": unknown_paths[:16],
        "max_stream_length": max_stream_length,
        **diagnostics,
    }
