"""Heartbeat schema + atomic writes for the Olympic Paints job wrapper."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_ROOT = Path(r"C:\Users\quint\.claude\heartbeats")
HISTORY_LIMIT = 100


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_latest(record: Dict[str, Any], root: Path = DEFAULT_ROOT) -> Path:
    """Write the latest-run heartbeat to <root>/<job_id>.json atomically."""
    job_id = record["job_id"]
    out = Path(root) / f"{job_id}.json"
    _atomic_write_json(out, record)
    return out


def append_history(record: Dict[str, Any], root: Path = DEFAULT_ROOT) -> Path:
    """Append record to <root>/<job_id>.history.jsonl, truncating to HISTORY_LIMIT entries."""
    job_id = record["job_id"]
    out = Path(root) / f"{job_id}.history.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)

    existing: List[str] = []
    if out.exists():
        existing = out.read_text(encoding="utf-8").splitlines()

    existing.append(json.dumps(record, ensure_ascii=False))
    trimmed = existing[-HISTORY_LIMIT:]

    fd, tmp = tempfile.mkstemp(
        prefix=out.name + ".",
        suffix=".tmp",
        dir=str(out.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("\n".join(trimmed) + "\n")
        os.replace(tmp, out)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    return out


def consume_summary(job_id: str, root: Path = DEFAULT_ROOT) -> Dict[str, Any] | None:
    """Read and delete <root>/_summary/<job_id>.json. Returns dict or None.

    Malformed JSON returns None and the file is still removed so it cannot poison
    the next run.
    """
    path = Path(root) / "_summary" / f"{job_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = None
    except json.JSONDecodeError:
        data = None
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    return data
