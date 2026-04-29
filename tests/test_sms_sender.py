"""Тесты для `adb.sms_sender`."""

import subprocess
from pathlib import Path

import pytest

from adb import sms_sender
from adb.companion import COMPANION_ACTION_SEND_SMS, COMPANION_COMMAND_RECEIVER
from adb.device_manager import AdbError
from adb.sms_sender import (
    install_companion,
    is_companion_installed,
    open_permission_screen,
    send_sms,
)

_FAKE_ADB = Path("C:/fake/adb.exe")


class _FakeCompleted:
    def __init__(self, returncode: int, stdout: bytes = b"", stderr: bytes = b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_send_sms_broadcasts_command_to_companion(monkeypatch):
    captured: dict = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return _FakeCompleted(0, b"Broadcast completed: result=0\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = send_sms(
        "+79990000000",
        "Привет Иван",
        request_id="req-1",
        auth_token="secret",
        adb_path=_FAKE_ADB,
        serial="SERIAL",
    )

    assert result.request_id == "req-1"
    assert captured["cmd"] == [
        str(_FAKE_ADB),
        "-s",
        "SERIAL",
        "shell",
        "am",
        "broadcast",
        "-a",
        COMPANION_ACTION_SEND_SMS,
        "-n",
        COMPANION_COMMAND_RECEIVER,
        "--es",
        "auth_token",
        "secret",
        "--es",
        "request_id",
        "req-1",
        "--es",
        "phone",
        "+79990000000",
        "--es",
        "message",
        "Привет Иван",
    ]
    assert captured["kwargs"]["capture_output"] is True


def test_send_sms_reads_auth_token_when_not_passed(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(sms_sender, "read_auth_token", lambda **kwargs: "from-device")

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return _FakeCompleted(0, b"ok")

    monkeypatch.setattr(subprocess, "run", fake_run)

    send_sms("+79990000000", "Text", request_id="req-2", adb_path=_FAKE_ADB)

    assert "from-device" in captured["cmd"]


def test_send_sms_rejects_empty_phone():
    with pytest.raises(ValueError, match="phone"):
        send_sms("", "Text", auth_token="secret", adb_path=_FAKE_ADB)


def test_send_sms_rejects_empty_message():
    with pytest.raises(ValueError, match="message"):
        send_sms("+79990000000", "", auth_token="secret", adb_path=_FAKE_ADB)


def test_is_companion_installed_returns_true(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: _FakeCompleted(0, b"package:/data/app/app.apk\n"),
    )

    assert is_companion_installed(adb_path=_FAKE_ADB) is True


def test_is_companion_installed_returns_false_on_missing_package(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: _FakeCompleted(1, b"", b"not found"),
    )

    assert is_companion_installed(adb_path=_FAKE_ADB) is False


def test_install_companion_raises_when_apk_missing(tmp_path):
    missing_apk = tmp_path / "missing.apk"

    with pytest.raises(AdbError, match="не найден"):
        install_companion(missing_apk, adb_path=_FAKE_ADB)


def test_open_permission_screen_starts_main_activity(monkeypatch):
    captured: dict = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return _FakeCompleted(0, b"Starting: Intent\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    open_permission_screen(adb_path=_FAKE_ADB)

    assert captured["cmd"][:4] == [str(_FAKE_ADB), "shell", "am", "start"]
