from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.config import get_settings

_writer_lock = Lock()


def _to_json_compatible(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(key): _to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [_to_json_compatible(item) for item in value]
    return str(value)


def _resolve_log_path() -> Path:
    settings = get_settings()
    return Path(settings.audit_log_path)


def append_audit_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    path = _resolve_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        **{key: _to_json_compatible(value) for key, value in payload.items()},
    }

    encoded = json.dumps(entry, ensure_ascii=True, separators=(",", ":"))
    with _writer_lock, path.open("a", encoding="utf-8") as handle:
        handle.write(encoded)
        handle.write("\n")

    return entry


def read_audit_events(limit: int) -> list[dict[str, Any]]:
    settings = get_settings()
    bounded_limit = min(max(limit, 1), settings.audit_export_max_lines)

    path = _resolve_log_path()
    if not path.exists():
        return []

    lines: deque[str] = deque(maxlen=bounded_limit)
    with _writer_lock, path.open("r", encoding="utf-8") as handle:
        for line in handle:
            content = line.strip()
            if content:
                lines.append(content)

    events: list[dict[str, Any]] = []
    for line in lines:
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            events.append(parsed)

    return events
