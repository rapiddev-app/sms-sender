"""Поиск подключённых Android-устройств через `adb.exe`.

Модуль инкапсулирует запуск `adb devices`, парсинг вывода и агрегацию
в высокоуровневый статус для GUI (Экран 3 — индикатор подключения).

`adb.exe` ищется в двух местах: в PyInstaller-бандле через `sys._MEIPASS`
и в `<project_root>/bin/adb/adb.exe` для dev-режима.
"""

import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

_ADB_TIMEOUT_SEC = 10
# Флаг Windows: подавить мелькание чёрного окна cmd при каждом subprocess-вызове.
_CREATE_NO_WINDOW = 0x08000000

_ADB_RELATIVE_PATH = Path("bin") / "adb" / "adb.exe"
# `device_manager.py` лежит в `src/adb/`, корень проекта — на 2 уровня выше.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class AdbNotFoundError(Exception):
    """`adb.exe` не найден ни в PyInstaller-бандле, ни в `bin/adb/`."""


class AdbError(Exception):
    """Сбой запуска adb: timeout, ненулевой exit code, нечитаемый вывод."""


class ConnectionState(Enum):
    """Высокоуровневое состояние подключения для GUI."""

    READY = "ready"
    NO_DEVICE = "no_device"
    UNAUTHORIZED = "unauthorized"
    OFFLINE = "offline"
    MULTIPLE_DEVICES = "multiple"
    ADB_NOT_FOUND = "adb_not_found"
    ADB_ERROR = "adb_error"


@dataclass(frozen=True)
class Device:
    """Запись из вывода `adb devices`."""

    serial: str
    state: str
    """Сырое состояние от adb: `device`, `unauthorized`, `offline`, и т.п."""


@dataclass(frozen=True)
class ConnectionStatus:
    """Агрегированный статус для GUI."""

    state: ConnectionState
    devices: list[Device] = field(default_factory=list)
    message: str = ""


def find_adb_executable() -> Path:
    """Возвращает путь к `adb.exe` или бросает `AdbNotFoundError`.

    Сначала проверяет `sys._MEIPASS` (режим PyInstaller-бандла), затем
    `<project_root>/bin/adb/adb.exe` (dev-режим).
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bundled = Path(meipass) / _ADB_RELATIVE_PATH
        if bundled.exists():
            return bundled

    dev_path = _PROJECT_ROOT / _ADB_RELATIVE_PATH
    if dev_path.exists():
        return dev_path

    raise AdbNotFoundError(
        f"adb.exe не найден. Ожидался путь: {dev_path}. "
        "Запустите `uv run scripts/fetch_adb.py` для скачивания."
    )


def list_devices(adb_path: Path | None = None) -> list[Device]:
    """Запускает `adb devices` и возвращает список устройств.

    Raises:
        AdbNotFoundError: `adb.exe` не найден.
        AdbError: timeout или ненулевой exit code.
    """
    executable = adb_path if adb_path is not None else find_adb_executable()

    try:
        result = subprocess.run(
            [str(executable), "devices"],
            capture_output=True,
            timeout=_ADB_TIMEOUT_SEC,
            creationflags=_CREATE_NO_WINDOW,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise AdbError(f"adb devices завис дольше {_ADB_TIMEOUT_SEC}с") from exc
    except OSError as exc:
        raise AdbError(f"Не удалось запустить adb: {exc}") from exc

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise AdbError(f"adb вернул код {result.returncode}: {stderr}")

    stdout = result.stdout.decode("utf-8", errors="replace")
    return _parse_devices_output(stdout)


def get_connection_status(adb_path: Path | None = None) -> ConnectionStatus:
    """Высокоуровневый статус для GUI — оборачивает ошибки в `ConnectionStatus`."""
    try:
        devices = list_devices(adb_path=adb_path)
    except AdbNotFoundError as exc:
        return ConnectionStatus(state=ConnectionState.ADB_NOT_FOUND, message=str(exc))
    except AdbError as exc:
        return ConnectionStatus(state=ConnectionState.ADB_ERROR, message=str(exc))

    if not devices:
        return ConnectionStatus(
            state=ConnectionState.NO_DEVICE,
            message="Телефон не обнаружен. Подключите устройство по USB и включите отладку.",
        )

    if len(devices) > 1:
        return ConnectionStatus(
            state=ConnectionState.MULTIPLE_DEVICES,
            devices=devices,
            message=(
                f"Подключено несколько устройств ({len(devices)}). "
                "Оставьте только одно — рассылка работает с одним телефоном."
            ),
        )

    device = devices[0]
    if device.state == "device":
        return ConnectionStatus(
            state=ConnectionState.READY,
            devices=devices,
            message=f"Устройство подключено: {device.serial}",
        )
    if device.state == "unauthorized":
        return ConnectionStatus(
            state=ConnectionState.UNAUTHORIZED,
            devices=devices,
            message=(
                "Устройство найдено, но требуется подтверждение USB-отладки на телефоне."
            ),
        )
    if device.state == "offline":
        return ConnectionStatus(
            state=ConnectionState.OFFLINE,
            devices=devices,
            message="Устройство в состоянии offline. Переподключите кабель.",
        )

    return ConnectionStatus(
        state=ConnectionState.ADB_ERROR,
        devices=devices,
        message=f"Неизвестное состояние устройства: {device.state}",
    )


def _parse_devices_output(stdout: str) -> list[Device]:
    """Парсит stdout `adb devices` в список устройств.

    Формат вывода:
        List of devices attached
        <serial>\\t<state>
        <serial>\\t<state>

    Все строки до маркера-заголовка и пустые — игнорируются.
    """
    devices: list[Device] = []
    header_seen = False

    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if not header_seen:
            if line.lower().startswith("list of devices"):
                header_seen = True
            continue

        # Формат строки: serial<tab>state[<tab>...metadata]
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        devices.append(Device(serial=serial, state=state))

    return devices
