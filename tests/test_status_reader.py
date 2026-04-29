"""Тесты для `adb.status_reader`."""

import subprocess
from pathlib import Path

import pytest

from adb.device_manager import AdbError
from adb.status_reader import read_statuses

_FAKE_ADB = Path("C:/fake/adb.exe")


class _FakeCompleted:
    def __init__(self, returncode: int, stdout: bytes = b"", stderr: bytes = b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_read_statuses_parses_jsonl_and_ignores_bad_lines(monkeypatch):
    stdout = (
        b'{"request_id":"req-1","phone":"+79990000000","state":"SENT",'
        b'"details":"","timestamp_ms":123}\n'
        b"bad json\n"
    )
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kwargs: _FakeCompleted(0, stdout))

    statuses = read_statuses(adb_path=_FAKE_ADB)

    assert len(statuses) == 1
    assert statuses[0].request_id == "req-1"
    assert statuses[0].state == "SENT"


def test_read_statuses_returns_empty_list_when_log_missing(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: _FakeCompleted(1, b"", b"No such file or directory"),
    )

    assert read_statuses(adb_path=_FAKE_ADB) == []


def test_read_statuses_raises_on_adb_error(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: _FakeCompleted(1, b"", b"run-as: package not debuggable"),
    )

    with pytest.raises(AdbError, match="run-as"):
        read_statuses(adb_path=_FAKE_ADB)
