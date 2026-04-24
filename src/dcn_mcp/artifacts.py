from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, Iterable

from .config import DEFAULT_ARTIFACT_ROOT
from .errors import ValidationError


def artifact_root() -> pathlib.Path:
    return pathlib.Path(DEFAULT_ARTIFACT_ROOT).expanduser().resolve()


def resolve_artifact_path(path: object) -> pathlib.Path:
    root = artifact_root()
    raw = str(path).strip()
    if not raw:
        raise ValidationError("Artifact path is required.", details={"path": "params.path"})
    candidate = pathlib.Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValidationError(
            "Artifact path must stay within the configured artifact root.",
            details={"artifact_root": str(root)},
        ) from exc
    if resolved == root:
        raise ValidationError("Artifact path must point to a file below the artifact root.", details={"artifact_root": str(root)})
    return resolved


def write_json(path: pathlib.Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def write_jsonl(path: pathlib.Path, records: Iterable[Dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")
    return str(path)
