"""Core task operations: the behaviour behind each CLI command.

This module knows nothing about printing or parsing arguments. It takes plain
values and returns plain values, and raises TaskNotFoundError or
StorageError when something goes wrong, so the CLI can turn those into exit
codes and messages.
"""

from __future__ import annotations

from . import storage
from .storage import STATUS_DONE, STATUS_IN_PROGRESS, STATUS_TODO, VALID_STATUSES


class TaskNotFoundError(Exception):
    """Raised when no task exists with the requested id."""


def _require_task(tasks: list[dict], task_id: int) -> dict:
    """Return the task with the given id, or raise TaskNotFoundError."""
    for task in tasks:
        if task.get("id") == task_id:
            return task
    raise TaskNotFoundError(f"Task with ID {task_id} not found.")


def next_id(tasks: list[dict]) -> int:
    """Return the next task id.

    The id is one more than the highest id currently in the list, so ids are
    handed out in increasing order. A deleted id is reused once nothing
    higher remains: with tasks 1 and 2 stored, deleting 2 and adding again
    gives the new task id 2. Ids are only guaranteed to be unique among the
    tasks that are currently in the file.
    """
    existing: set[int] = set()
    for task in tasks:
        try:
            existing.add(int(task.get("id", 0)))
        except (TypeError, ValueError):
            continue

    return max(existing, default=0) + 1


def add_task(
    description: str,
    tasks: list[dict] | None = None,
    path: str | None = None,
) -> dict:
    """Append a new task and return it.

    The task starts with status "todo" and both timestamps set to now.
    """
    description = (description or "").strip()
    if not description:
        raise ValueError("Task description cannot be empty.")

    tasks = list(tasks) if tasks is not None else storage.load_tasks(path)
    stamp = storage.now_iso()

    task = {
        "id": next_id(tasks),
        "description": description,
        "status": STATUS_TODO,
        "createdAt": stamp,
        "updatedAt": stamp,
    }
    tasks.append(task)
    storage.save_tasks(tasks, path)
    return task


def update_task(
    task_id: int,
    description: str,
    tasks: list[dict] | None = None,
    path: str | None = None,
) -> dict:
    """Change a task's description and return the updated task."""
    description = (description or "").strip()
    if not description:
        raise ValueError("Task description cannot be empty.")

    tasks = list(tasks) if tasks is not None else storage.load_tasks(path)
    task = _require_task(tasks, task_id)

    task["description"] = description
    task["updatedAt"] = storage.now_iso()
    storage.save_tasks(tasks, path)
    return task


def delete_task(
    task_id: int,
    tasks: list[dict] | None = None,
    path: str | None = None,
) -> dict:
    """Remove a task and return the task that was removed."""
    tasks = list(tasks) if tasks is not None else storage.load_tasks(path)
    task = _require_task(tasks, task_id)

    remaining = [item for item in tasks if item.get("id") != task_id]
    storage.save_tasks(remaining, path)
    return task


def set_status(
    task_id: int,
    status: str,
    tasks: list[dict] | None = None,
    path: str | None = None,
) -> dict:
    """Set a task's status and return the updated task."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Unknown status '{status}'.")

    tasks = list(tasks) if tasks is not None else storage.load_tasks(path)
    task = _require_task(tasks, task_id)

    task["status"] = status
    task["updatedAt"] = storage.now_iso()
    storage.save_tasks(tasks, path)
    return task


def mark_in_progress(
    task_id: int,
    tasks: list[dict] | None = None,
    path: str | None = None,
) -> dict:
    """Mark a task as in progress and return the updated task."""
    return set_status(task_id, STATUS_IN_PROGRESS, tasks, path)


def mark_done(
    task_id: int,
    tasks: list[dict] | None = None,
    path: str | None = None,
) -> dict:
    """Mark a task as done and return the updated task."""
    return set_status(task_id, STATUS_DONE, tasks, path)


def list_tasks(
    tasks: list[dict] | None = None,
    path: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """Return tasks ordered by id, optionally filtered by status."""
    tasks = list(tasks) if tasks is not None else storage.load_tasks(path)

    if status is None:
        selected = tasks
    else:
        selected = [task for task in tasks if task.get("status") == status]

    def sort_key(task: dict) -> tuple[int, int]:
        try:
            return (0, int(task.get("id", 0)))
        except (TypeError, ValueError):
            return (1, 0)

    return sorted(selected, key=sort_key)
