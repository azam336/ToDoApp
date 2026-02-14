"""JSON-file persistence with atomic writes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from src.models import TodoItem

DEFAULT_DB = "todo_data.json"


def _db_path() -> Path:
    return Path(os.environ.get("TODO_DB", DEFAULT_DB))


def load_items(path: Path | None = None) -> list[TodoItem]:
    """Load all to-do items from the JSON file."""
    p = path or _db_path()
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [TodoItem.from_dict(d) for d in data]


def save_items(items: list[TodoItem], path: Path | None = None) -> None:
    """Atomically save all to-do items to the JSON file."""
    p = path or _db_path()
    data = [item.to_dict() for item in items]
    # Write to a temp file in the same directory, then rename for atomicity.
    dir_ = p.parent or Path(".")
    dir_.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(dir_), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # On Windows, target must not exist for os.rename; use replace.
        os.replace(tmp, str(p))
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
