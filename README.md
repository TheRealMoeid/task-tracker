# Task Tracker CLI

A small command line tool to track what you need to do, what you are working on, and what you have finished. Tasks are stored in a JSON file in the current directory.

This project is based on the [Task Tracker](https://roadmap.sh/projects/task-tracker) challenge from roadmap.sh.

## Requirements

Python 3.13 or newer. No third party packages are needed to run the tool.

## Installation

```bash
git clone https://github.com/TheRealMoeid/task-tracker.git
cd task-tracker
py -3.13 -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

On macOS or Linux, replace the venv path with `.venv/bin/activate` and use `python3.13`.

## Usage

```bash
task-cli add "Buy groceries"
# Task added successfully (ID: 1)

task-cli update 1 "Buy groceries and cook dinner"
task-cli delete 1

task-cli mark-in-progress 1
task-cli mark-done 1

task-cli list
task-cli list done
task-cli list todo
task-cli list in-progress
```

## Commands

| Command | Description |
|---|---|
| `add <description>` | Add a new task |
| `update <id> <description>` | Change the description of a task |
| `delete <id>` | Remove a task |
| `mark-in-progress <id>` | Set a task's status to `in-progress` |
| `mark-done <id>` | Set a task's status to `done` |
| `list [done\|todo\|in-progress]` | List tasks, optionally filtered by status |

## Storage

Tasks live in `tasks.json` in the current directory. The file is created on first use.

Each task has these properties:

| Property | Description |
|---|---|
| `id` | Unique identifier |
| `description` | Short description of the task |
| `status` | `todo`, `in-progress`, or `done` |
| `createdAt` | When the task was created |
| `updatedAt` | When the task was last updated |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Command succeeded |
| `1` | Task not found, storage problem, or other failure |
| `2` | Invalid or missing arguments |

## Running the tests

```bash
python -m pytest -v
```

All tests are self contained and do not touch the network or the real `tasks.json`.

## Limitations

- One flat list of tasks, no projects, tags, priorities, or due dates
- No pagination or search
- Task IDs are not reused after a task is deleted
