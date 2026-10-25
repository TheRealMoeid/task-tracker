"""Shared pytest fixtures for the Task Tracker test suite."""

from __future__ import annotations

import pytest

from task_tracker import cli


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Run a command against a throwaway tasks.json and capture the output.

    Returns a helper that takes argv, runs the CLI with the working directory
    pointed at a temp folder, and gives back (exit_code, stdout, stderr, path).
    """
    def run(*argv: str):
        import contextlib
        import io

        out, err = io.StringIO(), io.StringIO()
        monkeypatch.chdir(tmp_path)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue(), tmp_path / "tasks.json"

    return run


@pytest.fixture
def tasks_file(tmp_path):
    """Return the path of the tasks.json file inside a temp directory."""
    return tmp_path / "tasks.json"
