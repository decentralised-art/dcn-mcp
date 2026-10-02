from __future__ import annotations

from typing import List, Sequence, Tuple, TypeVar

from .errors import ValidationError


T = TypeVar("T")


DEFAULT_TOOLS_PAGE_SIZE = 10
DEFAULT_RESOURCES_PAGE_SIZE = 10


def parse_cursor(cursor: str | None) -> int:
    if cursor is None or str(cursor).strip() == "":
        return 0
    raw = str(cursor).strip()
    if not raw.isdigit():
        raise ValidationError("cursor must be a non-negative integer string", details={"cursor": raw})
    return int(raw)


def paginate(items: Sequence[T], cursor: str | None, *, page_size: int) -> Tuple[List[T], str | None]:
    start = parse_cursor(cursor)
    if start < 0:
        raise ValidationError("cursor must be non-negative", details={"cursor": cursor})
    end = start + int(page_size)
    page = list(items[start:end])
    next_cursor = str(end) if end < len(items) else None
    return page, next_cursor
