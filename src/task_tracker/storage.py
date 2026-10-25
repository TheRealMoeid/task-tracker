"""Storage for tasks: reading and writing the tasks.json file.

The file lives in the current directory and is created on first use. Only the
Python standard library is used, as required by the roadmap.sh Task Tracker
project.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_FILE_NAME = "tasks.json"

#: The statuses a task can have.
STATUS_TODO = "todo"
STATUS_IN_PROGRESS = "in-progress"
STATUS_DONE = "done"
VALID_STATUSES = (STATUS_TODO, STATUS_IN_PROGRESS, STATUS_DONE)

#: The properties every task must have.
REQUIRED_FIELDS = ("id", "description", "status", "createdAt", "updatedAt")


class StorageError(Exception):
    """Raised when the task file cannot be read, parsed, or written."""


def now_iso() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def default_file_path() -> Path:
    """Return the path of the task file in the current directory."""
    return Path.cwd() / DEFAULT_FILE_NAME


def load_tasks(path: Path | str | None = None) -> list[dict]:
    """Load tasks from the task file.

    Returns an empty list when the file does not exist, so callers can start
    from a clean slate. Raises StorageError when the file exists but cannot be
    read or does not contain a JSON list.
    """
    target = Path(path) if path is not None else default_file_path()

    if not target.exists():
        return []

    try:
        raw = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise StorageError(f"Could not read {target}: {exc.strerror}") from exc

    if not raw.strip():
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StorageError(
            f"Could not read {target}: the file is not valid JSON."
        ) from exc

    if not isinstance(data, list):
        raise StorageError(
            f"Could not read {target}: expected a list of tasks at the top level."
        )

    return data


def save_tasks(tasks: list[dict], path: Path | str | None = None) -> None:
    """Write tasks to the task file, creating or replacing it.

    Raises StorageError when the file cannot be written, for example because
    the directory is not writable.
    """
    target = Path(path) if path is not None else default_file_path()

    try:
        target.write_text(
            json.dumps(tasks, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise StorageError(f"Could not write {target}: {exc.strerror}") from exc


def file_exists(path: Path | str | None = None) -> bool:
    """Return True when the task file already exists."""
    target = Path(path) if path is not None else default_file_path()
    return target.exists()
