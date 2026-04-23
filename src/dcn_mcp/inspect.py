from __future__ import annotations

from typing import Any, Dict, List, Tuple


def sample_path(sample: Dict[str, Any]) -> str:
    return str(sample.get("path") or sample.get("feature_path") or "").strip()


def strip_index_suffix(segment: str) -> str:
    head, sep, tail = str(segment).rpartition(":")
    if sep and tail.isdigit():
        return head
    return str(segment)


def group_samples_by_parent(samples: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, List[int]]], List[str]]:
    grouped: Dict[str, Dict[str, List[int]]] = {}
    unknown_paths: List[str] = []
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
        group_key = "/" + "/".join(strip_index_suffix(segment) for segment in segments[:-1]) if len(segments) > 1 else "/root"
        values: List[int] = []
        for item in list(sample.get("data") or []):
            try:
                values.append(int(item))
            except Exception:
                pass
        grouped.setdefault(group_key, {})[leaf] = values
    return grouped, unknown_paths


def summarize_samples(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped, unknown_paths = group_samples_by_parent(samples)
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
    }
