from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def parse_runtime_trace_line(raw: str) -> dict[str, Any] | None:
    """Normalize one JSONL runtime call event into caller/callee fields."""
    text = raw.strip()
    if not text or text.startswith("#"):
        return None
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    caller = (
        obj.get("caller")
        or obj.get("from")
        or obj.get("source")
        or obj.get("frame")
    )
    callee = (
        obj.get("callee")
        or obj.get("to")
        or obj.get("target")
        or obj.get("name")
    )
    if not caller or not callee:
        return None
    return {
        "caller": str(caller),
        "callee": str(callee),
        "count": int(obj.get("count") or 1),
        "ts": obj.get("ts") or obj.get("timestamp"),
    }


def load_runtime_trace_file(path: Path, *, limit: int = 5000) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if len(events) >= limit:
                break
            parsed = parse_runtime_trace_line(line)
            if parsed:
                events.append(parsed)
    return events
