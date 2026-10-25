"""Command line interface for the Task Tracker.

Parses positional arguments, calls into task_tracker.tasks, prints the result,
and turns failures into exit codes:

    0  the command succeeded
    1  a task was not found, or the task file could not be read or written
    2  the arguments were missing, extra, blank, or not understood
"""

from __future__ import annotations

import sys

from . import tasks
from .storage import StorageError
from .tasks import TaskNotFoundError

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2

USAGE = """Usage:
  task-cli add <description>
  task-cli update <id> <description>
  task-cli delete <id>
  task-cli mark-in-progress <id>
  task-cli mark-done <id>
  task-cli list [done|todo|in-progress]
"""


def _parse_id(raw: str) -> int | None:
    """Return the id in raw as an int, or None when it is not a whole number."""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _fail(message: str, code: int = EXIT_FAILURE) -> int:
    """Print an error to stderr and return the exit code."""
    print(f"Error: {message}", file=sys.stderr)
    return code


def cmd_add(arguments: list[str]) -> int:
    """Handle `add <description>`. The description may contain spaces."""
    if not arguments:
        return _fail("Missing task description.", EXIT_USAGE)
    if len(arguments) > 1:
        return _fail("Too many arguments for 'add'.", EXIT_USAGE)

    description = arguments[0].strip()
    if not description:
        return _fail("Missing task description.", EXIT_USAGE)

    try:
        task = tasks.add_task(description)
    except (StorageError, ValueError) as exc:
        return _fail(str(exc))

    print(f"Task added successfully (ID: {task['id']})")
    return EXIT_OK


def cmd_update(arguments: list[str]) -> int:
    """Handle `update <id> <description>`."""
    if len(arguments) < 2:
        return _fail("Usage: task-cli update <id> <description>", EXIT_USAGE)

    task_id = _parse_id(arguments[0])
    if task_id is None:
        return _fail(f"'{arguments[0]}' is not a valid task ID.", EXIT_USAGE)

    description = arguments[1].strip()
    if not description:
        return _fail("Missing task description.", EXIT_USAGE)

    try:
        task = tasks.update_task(task_id, description)
    except TaskNotFoundError as exc:
        return _fail(str(exc))
    except (StorageError, ValueError) as exc:
        return _fail(str(exc))

    print(f"Task {task['id']} updated successfully")
    return EXIT_OK


def cmd_delete(arguments: list[str]) -> int:
    """Handle `delete <id>`."""
    if len(arguments) != 1:
        return _fail("Usage: task-cli delete <id>", EXIT_USAGE)

    task_id = _parse_id(arguments[0])
    if task_id is None:
        return _fail(f"'{arguments[0]}' is not a valid task ID.", EXIT_USAGE)

    try:
        task = tasks.delete_task(task_id)
    except TaskNotFoundError as exc:
        return _fail(str(exc))
    except StorageError as exc:
        return _fail(str(exc))

    print(f"Task {task['id']} deleted successfully")
    return EXIT_OK


def cmd_mark(arguments: list[str], command: str, status: str) -> int:
    """Handle `mark-in-progress <id>` and `mark-done <id>`."""
    if len(arguments) != 1:
        return _fail(f"Usage: task-cli {command} <id>", EXIT_USAGE)

    task_id = _parse_id(arguments[0])
    if task_id is None:
        return _fail(f"'{arguments[0]}' is not a valid task ID.", EXIT_USAGE)

    try:
        task = tasks.set_status(task_id, status)
    except TaskNotFoundError as exc:
        return _fail(str(exc))
    except (StorageError, ValueError) as exc:
        return _fail(str(exc))

    label = status.replace("-", " ")
    print(f"Task {task['id']} marked as {label}")
    return EXIT_OK


def cmd_list(arguments: list[str]) -> int:
    """Handle `list` and `list <status>`."""
    if len(arguments) > 1:
        return _fail("Too many arguments for 'list'.", EXIT_USAGE)

    status = arguments[0] if arguments else None
    if status is not None and status not in tasks.VALID_STATUSES:
        return _fail(
            f"Unknown status '{status}'. Use todo, in-progress, or done.",
            EXIT_USAGE,
        )

    try:
        selected = tasks.list_tasks(status=status)
    except StorageError as exc:
        return _fail(str(exc))

    if not selected:
        if status is None:
            print("No tasks yet. Add one with: task-cli add <description>")
        else:
            print(f"No tasks with status '{status}'.")
        return EXIT_OK

    for task in selected:
        description = task.get("description", "")
        print(f"[{task.get('status', '?')}] {task.get('id')}. {description}")

    return EXIT_OK


COMMANDS = {
    "add": cmd_add,
    "update": cmd_update,
    "delete": cmd_delete,
    "list": cmd_list,
}


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    arguments = list(sys.argv[1:] if argv is None else argv)

    if not arguments:
        print(USAGE, file=sys.stderr)
        return EXIT_USAGE

    command = arguments[0]
    rest = arguments[1:]

    if command in ("mark-in-progress", "mark-done"):
        status = "in-progress" if command == "mark-in-progress" else "done"
        return cmd_mark(rest, command, status)

    handler = COMMANDS.get(command)
    if handler is None:
        print(f"Error: Unknown command '{command}'.\n", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return EXIT_USAGE

    return handler(rest)


if __name__ == "__main__":
    raise SystemExit(main())
