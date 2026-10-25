"""Tests for the storage layer."""

from __future__ import annotations

import json

import pytest

from task_tracker import storage


def test_missing_file_returns_empty_list(tmp_path):
    assert storage.load_tasks(tmp_path / "tasks.json") == []


def test_missing_file_is_not_created(tmp_path):
    storage.load_tasks(tmp_path / "tasks.json")
    assert not (tmp_path / "tasks.json").exists()


def test_save_creates_the_file(tmp_path):
    path = tmp_path / "tasks.json"
    storage.save_tasks([{"id": 1}], path)
    assert path.exists()


def test_round_trip_preserves_tasks(tmp_path):
    path = tmp_path / "tasks.json"
    original = [{"id": 1, "description": "x", "status": "todo"}]
    storage.save_tasks(original, path)
    assert storage.load_tasks(path) == original


def test_empty_file_returns_empty_list(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text("", encoding="utf-8")
    assert storage.load_tasks(path) == []


def test_whitespace_only_file_returns_empty_list(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text("   \n", encoding="utf-8")
    assert storage.load_tasks(path) == []


def test_invalid_json_raises_storage_error(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(storage.StorageError):
        storage.load_tasks(path)


def test_non_list_json_raises_storage_error(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps({"id": 1}), encoding="utf-8")
    with pytest.raises(storage.StorageError):
        storage.load_tasks(path)


def test_write_failure_raises_storage_error(tmp_path):
    # A directory in place of a file cannot be written as a file.
    target = tmp_path / "blocked"
    target.mkdir()
    with pytest.raises(storage.StorageError):
        storage.save_tasks([{"id": 1}], target)


def test_default_path_is_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert storage.default_file_path() == tmp_path / "tasks.json"


def test_timestamps_are_iso8601():
    stamp = storage.now_iso()
    assert "T" in stamp
    assert stamp.endswith("+00:00")
