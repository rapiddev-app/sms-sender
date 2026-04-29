"""Тесты для `adb.device_manager`.

`subprocess.run` мокается через `monkeypatch` — реальный `adb.exe` не запускается.
Поиск `adb.exe` в тестах обходится передачей `adb_path` явно.
"""

import subprocess
from pathlib import Path

import pytest

from adb import device_manager
from adb.device_manager import (
    AdbError,
    AdbNotFoundError,
    ConnectionState,
    Device,
    _parse_devices_output,
    find_adb_executable,
    get_connection_status,
    list_devices,
)

_FAKE_ADB = Path("C:/fake/adb.exe")


# ---------- _parse_devices_output ----------

def test_parse_devices_output_returns_empty_for_no_devices():
    output = "List of devices attached\n\n"
    assert _parse_devices_output(output) == []


def test_parse_devices_output_returns_one_device():
    output = "List of devices attached\nABC123\tdevice\n"
    assert _parse_devices_output(output) == [Device(serial="ABC123", state="device")]


def test_parse_devices_output_returns_multiple_devices():
    output = (
        "List of devices attached\n"
        "ABC123\tdevice\n"
        "XYZ789\tunauthorized\n"
    )
    assert _parse_devices_output(output) == [
        Device(serial="ABC123", state="device"),
        Device(serial="XYZ789", state="unauthorized"),
    ]


def test_parse_devices_output_recognizes_unauthorized_state():
    output = "List of devices attached\nSERIAL1\tunauthorized\n"
    assert _parse_devices_output(output) == [Device(serial="SERIAL1", state="unauthorized")]


def test_parse_devices_output_ignores_lines_before_header():
    output = (
        "* daemon not running; starting now at tcp:5037\n"
        "* daemon started successfully\n"
        "List of devices attached\n"
        "ABC123\tdevice\n"
    )
    assert _parse_devices_output(output) == [Device(serial="ABC123", state="device")]


def test_parse_devices_output_handles_metadata_columns():
    # adb -l добавляет product/model/transport_id — мы их не используем, но не должны падать.
    output = (
        "List of devices attached\n"
        "ABC123\tdevice product:foo model:bar transport_id:1\n"
    )
    assert _parse_devices_output(output) == [Device(serial="ABC123", state="device")]


# ---------- list_devices ----------

class _FakeCompleted:
    def __init__(self, returncode: int, stdout: bytes = b"", stderr: bytes = b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_list_devices_invokes_subprocess_with_adb_path(monkeypatch):
    captured: dict = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return _FakeCompleted(0, b"List of devices attached\nABC\tdevice\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    devices = list_devices(adb_path=_FAKE_ADB)

    assert devices == [Device(serial="ABC", state="device")]
    assert captured["cmd"] == [str(_FAKE_ADB), "devices"]
    assert captured["kwargs"]["timeout"] == 10
    assert captured["kwargs"]["capture_output"] is True


def test_list_devices_raises_adb_error_on_timeout(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=10)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(AdbError, match="завис"):
        list_devices(adb_path=_FAKE_ADB)


def test_list_devices_raises_adb_error_on_nonzero_exit(monkeypatch):
    def fake_run(cmd, **kwargs):
        return _FakeCompleted(1, b"", b"adb: something is wrong")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(AdbError, match="код 1"):
        list_devices(adb_path=_FAKE_ADB)


def test_list_devices_raises_adb_error_on_oserror(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(AdbError, match="permission denied"):
        list_devices(adb_path=_FAKE_ADB)


def test_list_devices_calls_find_adb_executable_when_path_not_given(monkeypatch):
    monkeypatch.setattr(device_manager, "find_adb_executable", lambda: _FAKE_ADB)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kwargs: _FakeCompleted(0, b"List of devices attached\n"),
    )

    assert list_devices() == []


# ---------- get_connection_status ----------

def _patch_list(monkeypatch, devices: list[Device]) -> None:
    monkeypatch.setattr(device_manager, "list_devices", lambda adb_path=None: devices)


def test_get_connection_status_ready_when_one_device(monkeypatch):
    _patch_list(monkeypatch, [Device("ABC", "device")])
    status = get_connection_status()
    assert status.state == ConnectionState.READY
    assert status.devices == [Device("ABC", "device")]
    assert "ABC" in status.message


def test_get_connection_status_no_device_when_list_empty(monkeypatch):
    _patch_list(monkeypatch, [])
    status = get_connection_status()
    assert status.state == ConnectionState.NO_DEVICE
    assert status.devices == []


def test_get_connection_status_unauthorized(monkeypatch):
    _patch_list(monkeypatch, [Device("ABC", "unauthorized")])
    status = get_connection_status()
    assert status.state == ConnectionState.UNAUTHORIZED


def test_get_connection_status_offline(monkeypatch):
    _patch_list(monkeypatch, [Device("ABC", "offline")])
    status = get_connection_status()
    assert status.state == ConnectionState.OFFLINE


def test_get_connection_status_multiple_devices(monkeypatch):
    _patch_list(monkeypatch, [Device("A", "device"), Device("B", "device")])
    status = get_connection_status()
    assert status.state == ConnectionState.MULTIPLE_DEVICES
    assert len(status.devices) == 2


def test_get_connection_status_unknown_state(monkeypatch):
    _patch_list(monkeypatch, [Device("ABC", "bootloader")])
    status = get_connection_status()
    assert status.state == ConnectionState.ADB_ERROR
    assert "bootloader" in status.message


def test_get_connection_status_adb_not_found(monkeypatch):
    def raise_not_found(adb_path=None):
        raise AdbNotFoundError("nope")

    monkeypatch.setattr(device_manager, "list_devices", raise_not_found)
    status = get_connection_status()
    assert status.state == ConnectionState.ADB_NOT_FOUND
    assert status.message == "nope"


def test_get_connection_status_adb_error(monkeypatch):
    def raise_adb_error(adb_path=None):
        raise AdbError("timeout")

    monkeypatch.setattr(device_manager, "list_devices", raise_adb_error)
    status = get_connection_status()
    assert status.state == ConnectionState.ADB_ERROR
    assert status.message == "timeout"


# ---------- find_adb_executable ----------

def test_find_adb_executable_returns_dev_path_when_exists(monkeypatch, tmp_path):
    fake_root = tmp_path
    adb_dir = fake_root / "bin" / "adb"
    adb_dir.mkdir(parents=True)
    adb_file = adb_dir / "adb.exe"
    adb_file.write_bytes(b"")

    monkeypatch.setattr(device_manager, "_PROJECT_ROOT", fake_root)
    # На случай, если тесты запускаются из бандла — сбрасываем _MEIPASS.
    monkeypatch.delattr("sys._MEIPASS", raising=False)

    assert find_adb_executable() == adb_file


def test_find_adb_executable_raises_when_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(device_manager, "_PROJECT_ROOT", tmp_path)
    monkeypatch.delattr("sys._MEIPASS", raising=False)

    with pytest.raises(AdbNotFoundError, match="adb.exe не найден"):
        find_adb_executable()


def test_find_adb_executable_prefers_meipass_when_set(monkeypatch, tmp_path):
    import sys as _sys

    bundle_root = tmp_path / "bundle"
    bundle_adb = bundle_root / "bin" / "adb" / "adb.exe"
    bundle_adb.parent.mkdir(parents=True)
    bundle_adb.write_bytes(b"")

    monkeypatch.setattr(_sys, "_MEIPASS", str(bundle_root), raising=False)
    # dev-путь специально не создаём — должен сработать meipass.
    monkeypatch.setattr(device_manager, "_PROJECT_ROOT", tmp_path / "nonexistent")

    assert find_adb_executable() == bundle_adb
