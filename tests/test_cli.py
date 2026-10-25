"""End to end tests for the CLI, driving it the way a user would."""

from __future__ import annotations

import json

import pytest

from task_tracker.cli import EXIT_FAILURE, EXIT_OK, EXIT_USAGE


def test_no_arguments_prints_usage_and_exits_two(store):
    code, out, err, _ = store()
    assert code == EXIT_USAGE
    assert out == ""
    assert "Usage:" in err


def test_unknown_command_exits_two(store):
    code, out, err, _ = store("frobnicate")
    assert code == EXIT_USAGE
    assert "Unknown command 'frobnicate'" in err


def test_add_creates_the_file_and_reports_the_id(store):
    code, out, err, path = store("add", "Buy groceries")
    assert code == EXIT_OK
    assert err == ""
    assert out.strip() == "Task added successfully (ID: 1)"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data[0]["description"] == "Buy groceries"
    assert data[0]["status"] == "todo"
    assert set(data[0]) == {"id", "description", "status", "createdAt", "updatedAt"}


def test_add_allows_descriptions_with_spaces(store):
    code, out, _, path = store("add", "Buy groceries and cook dinner")
    assert code == EXIT_OK
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data[0]["description"] == "Buy groceries and cook dinner"


def test_add_without_description_exits_two(store):
    code, out, err, _ = store("add")
    assert code == EXIT_USAGE
    assert "Missing task description" in err


def test_add_with_blank_description_exits_two(store):
    code, _, err, _ = store("add", "   ")
    assert code == EXIT_USAGE
    assert "Missing task description" in err


def test_add_with_too_many_arguments_exits_two(store):
    code, _, err, _ = store("add", "one", "two")
    assert code == EXIT_USAGE
    assert "Too many arguments" in err


def test_update_changes_the_description(store):
    store("add", "Buy groceries")
    code, out, _, path = store("update", "1", "Buy groceries and cook dinner")
    assert code == EXIT_OK
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data[0]["description"] == "Buy groceries and cook dinner"


def test_update_bumps_updated_at(store):
    store("add", "Buy groceries")
    code, _, _, path = store("update", "1", "New description")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert code == EXIT_OK
    assert data[0]["updatedAt"] >= data[0]["createdAt"]


def test_update_with_bad_id_exits_two(store):
    store("add", "Buy groceries")
    code, _, err, _ = store("update", "abc", "New description")
    assert code == EXIT_USAGE
    assert "not a valid task ID" in err


def test_update_unknown_id_exits_one(store):
    store("add", "Buy groceries")
    code, _, err, _ = store("update", "99", "New description")
    assert code == EXIT_FAILURE
    assert "not found" in err


def test_delete_removes_the_task(store):
    store("add", "Buy groceries")
    code, out, _, path = store("delete", "1")
    assert code == EXIT_OK
    assert json.loads(path.read_text(encoding="utf-8")) == []


def test_delete_unknown_id_exits_one(store):
    store("add", "Buy groceries")
    code, _, err, _ = store("delete", "99")
    assert code == EXIT_FAILURE
    assert "not found" in err


def test_delete_with_extra_arguments_exits_two(store):
    store("add", "Buy groceries")
    code, _, err, _ = store("delete", "1", "2")
    assert code == EXIT_USAGE


def test_mark_in_progress(store):
    store("add", "Buy groceries")
    code, _, _, path = store("mark-in-progress", "1")
    assert code == EXIT_OK
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data[0]["status"] == "in-progress"


def test_mark_done(store):
    store("add", "Buy groceries")
    code, _, _, path = store("mark-done", "1")
    assert code == EXIT_OK
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data[0]["status"] == "done"


def test_mark_unknown_id_exits_one(store):
    store("add", "Buy groceries")
    code, _, err, _ = store("mark-done", "99")
    assert code == EXIT_FAILURE
    assert "not found" in err


def test_list_shows_all_tasks(store):
    store("add", "first")
    store("add", "second")
    code, out, _, _ = store("list")
    assert code == EXIT_OK
    assert "1. first" in out
    assert "2. second" in out


def test_list_done_filters(store):
    store("add", "todo task")
    store("add", "done task")
    store("mark-done", "2")
    code, out, _, _ = store("list", "done")
    assert code == EXIT_OK
    assert "done task" in out
    assert "todo task" not in out


def test_list_in_progress_filters(store):
    store("add", "todo task")
    store("add", "progress task")
    store("mark-in-progress", "2")
    code, out, _, _ = store("list", "in-progress")
    assert code == EXIT_OK
    assert "progress task" in out
    assert "todo task" not in out


def test_list_todo_filters(store):
    store("add", "todo task")
    store("add", "done task")
    store("mark-done", "2")
    code, out, _, _ = store("list", "todo")
    assert code == EXIT_OK
    assert "todo task" in out
    assert "done task" not in out


def test_list_with_unknown_status_exits_two(store):
    store("add", "task")
    code, _, err, _ = store("list", "bogus")
    assert code == EXIT_USAGE
    assert "Unknown status 'bogus'" in err


def test_list_on_empty_store_succeeds(store):
    code, out, err, _ = store("list")
    assert code == EXIT_OK
    assert err == ""
    assert "No tasks yet" in out


def test_list_with_no_match_succeeds(store):
    store("add", "todo task")
    code, out, err, _ = store("list", "done")
    assert code == EXIT_OK
    assert err == ""
    assert "No tasks with status 'done'" in out


def test_results_go_to_stdout_and_errors_to_stderr(store):
    code, out, err, _ = store("delete", "99")
    assert code == EXIT_FAILURE
    assert out == ""
    assert err.startswith("Error:")


def test_state_persists_across_invocations(store):
    store("add", "first")
    store("add", "second")
    code, out, _, _ = store("list")
    assert code == EXIT_OK
    assert out.count("\n") == 2


def test_id_fills_the_highest_free_slot(store):
    store("add", "first")
    store("add", "second")
    store("delete", "2")
    code, out, _, _ = store("add", "third")
    assert code == EXIT_OK
    assert "(ID: 2)" in out


def test_description_is_stored_verbatim(store):
    store("add", "  padded  ")
    _, out, _, path = store("list")
    assert "padded" in out
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data[0]["description"] == "padded"


def test_full_workflow_from_the_spec(store):
    """Walk through the exact example sequence from roadmap.sh."""
    assert store("add", "Buy groceries")[0] == EXIT_OK
    assert store("update", "1", "Buy groceries and cook dinner")[0] == EXIT_OK
    assert store("delete", "1")[0] == EXIT_OK
    code, out, err, path = store("list")
    assert (code, err) == (EXIT_OK, "")
    assert json.loads(path.read_text(encoding="utf-8")) == []


def test_unicode_description_round_trips(store):
    store("add", "خرید مواد غذایی")
    code, out, _, path = store("list")
    assert code == EXIT_OK
    assert "خرید مواد غذایی" in out
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data[0]["description"] == "خرید مواد غذایی"


def test_corrupt_file_reports_an_error_instead_of_crashing(store, tasks_file):
    tasks_file.write_text("{oops", encoding="utf-8")
    code, out, err, _ = store("list")
    assert code == EXIT_FAILURE
    assert out == ""
    assert "not valid JSON" in err


def test_non_list_file_reports_an_error(store, tasks_file):
    tasks_file.write_text('{"id": 1}', encoding="utf-8")
    code, _, err, _ = store("list")
    assert code == EXIT_FAILURE
    assert "expected a list" in err
