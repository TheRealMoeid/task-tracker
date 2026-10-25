"""Tests for the core task operations."""

from __future__ import annotations

import pytest

from task_tracker import tasks
from task_tracker.storage import STATUS_DONE, STATUS_IN_PROGRESS, STATUS_TODO


def test_add_assigns_incrementing_ids(tmp_path):
    path = tmp_path / "tasks.json"
    first = tasks.add_task("one", path=str(path))
    second = tasks.add_task("two", path=str(path))
    assert first["id"] == 1
    assert second["id"] == 2


def test_add_starts_as_todo_with_both_timestamps(tmp_path):
    path = tmp_path / "tasks.json"
    task = tasks.add_task("buy milk", path=str(path))
    assert task["status"] == STATUS_TODO
    assert task["createdAt"]
    assert task["updatedAt"] == task["createdAt"]


def test_add_writes_to_the_file(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("buy milk", path=str(path))
    loaded = tasks.list_tasks(path=str(path))
    assert len(loaded) == 1
    assert loaded[0]["description"] == "buy milk"


def test_add_rejects_empty_description():
    with pytest.raises(ValueError):
        tasks.add_task("   ", tasks=[])


def test_add_rejects_blank_description_with_only_spaces():
    with pytest.raises(ValueError):
        tasks.add_task("  \n\t ", tasks=[])


def test_update_changes_description_and_updated_at(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("old", path=str(path))
    updated = tasks.update_task(1, "new", path=str(path))
    assert updated["description"] == "new"
    assert updated["status"] == STATUS_TODO


def test_update_unknown_id_raises(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("old", path=str(path))
    with pytest.raises(tasks.TaskNotFoundError):
        tasks.update_task(99, "new", path=str(path))


def test_update_rejects_empty_description(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("old", path=str(path))
    with pytest.raises(ValueError):
        tasks.update_task(1, "   ", path=str(path))


def test_delete_removes_only_that_task(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("one", path=str(path))
    tasks.add_task("two", path=str(path))
    removed = tasks.delete_task(1, path=str(path))
    assert removed["description"] == "one"
    remaining = tasks.list_tasks(path=str(path))
    assert [t["description"] for t in remaining] == ["two"]


def test_delete_unknown_id_raises(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("one", path=str(path))
    with pytest.raises(tasks.TaskNotFoundError):
        tasks.delete_task(42, path=str(path))


def test_ids_never_collide_with_existing_tasks(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("one", path=str(path))
    tasks.add_task("two", path=str(path))
    tasks.delete_task(2, path=str(path))
    next_task = tasks.add_task("three", path=str(path))
    assert next_task["id"] == 2
    assert len(tasks.list_tasks(path=str(path))) == 2


def test_set_status_updates_status(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("one", path=str(path))
    task = tasks.set_status(1, STATUS_DONE, path=str(path))
    assert task["status"] == STATUS_DONE


def test_mark_in_progress_and_done_helpers(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("one", path=str(path))
    assert tasks.mark_in_progress(1, path=str(path))["status"] == STATUS_IN_PROGRESS
    assert tasks.mark_done(1, path=str(path))["status"] == STATUS_DONE


def test_set_status_rejects_unknown_status(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("one", path=str(path))
    with pytest.raises(ValueError):
        tasks.set_status(1, "nope", path=str(path))


def test_set_status_unknown_id_raises(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("one", path=str(path))
    with pytest.raises(tasks.TaskNotFoundError):
        tasks.mark_done(7, path=str(path))


def test_list_returns_all_tasks_ordered_by_id(tmp_path):
    path = tmp_path / "tasks.json"
    for name in ["c", "a", "b"]:
        tasks.add_task(name, path=str(path))
    assert [t["id"] for t in tasks.list_tasks(path=str(path))] == [1, 2, 3]


def test_list_filters_by_status(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("todo task", path=str(path))
    tasks.add_task("progress task", path=str(path))
    tasks.add_task("done task", path=str(path))
    tasks.mark_in_progress(2, path=str(path))
    tasks.mark_done(3, path=str(path))

    assert [t["id"] for t in tasks.list_tasks(path=str(path), status=STATUS_TODO)] == [1]
    assert [t["id"] for t in tasks.list_tasks(path=str(path), status=STATUS_IN_PROGRESS)] == [2]
    assert [t["id"] for t in tasks.list_tasks(path=str(path), status=STATUS_DONE)] == [3]


def test_list_with_no_match_returns_empty(tmp_path):
    path = tmp_path / "tasks.json"
    tasks.add_task("todo task", path=str(path))
    assert tasks.list_tasks(path=str(path), status=STATUS_DONE) == []


def test_next_id_handles_empty_list():
    assert tasks.next_id([]) == 1


def test_next_id_ignores_malformed_ids():
    assert tasks.next_id([{"id": "x"}, {"id": None}]) == 1


def test_operations_do_not_depend_on_order():
    tasks_list = [{"id": 5, "description": "a", "status": "todo"}]
    assert tasks.next_id(tasks_list) == 6
