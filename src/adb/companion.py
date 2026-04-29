"""Общие утилиты ADB для Android-приложения-компаньона."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from adb.device_manager import AdbError, find_adb_executable

_ADB_TIMEOUT_SEC = 15
_CREATE_NO_WINDOW = 0x08000000
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

COMPANION_PACKAGE = "com.smsauto.companion"
COMPANION_ACTION_SEND_SMS = f"{COMPANION_PACKAGE}.action.SEND_SMS"
COMPANION_MAIN_ACTIVITY = f"{COMPANION_PACKAGE}/.MainActivity"
COMPANION_COMMAND_RECEIVER = f"{COMPANION_PACKAGE}/.SmsCommandReceiver"
COMPANION_APK_RELATIVE_PATH = (
    Path("android") / "sms_companion" / "app" / "build" / "outputs" / "apk" / "debug"
    / "app-debug.apk"
)


@dataclass(frozen=True)
class AdbCommandResult:
    """Результат выполнения ADB-команды."""

    returncode: int
    stdout: str
    stderr: str


def find_companion_apk() -> Path:
    """Возвращает ожидаемый путь к debug APK Android-компаньона."""
    return _PROJECT_ROOT / COMPANION_APK_RELATIVE_PATH


def run_adb(
    args: Sequence[str],
    *,
    adb_path: Path | None = None,
    serial: str | None = None,
    timeout: int = _ADB_TIMEOUT_SEC,
    check: bool = True,
) -> AdbCommandResult:
    """Запускает `adb` с общими настройками проекта.

    Args:
        args: Аргументы после `adb`.
        adb_path: Явный путь к `adb.exe`; если не задан, используется поиск проекта.
        serial: Серийный номер устройства для `adb -s <serial>`.
        timeout: Таймаут выполнения в секундах.
        check: Бросать `AdbError`, если `adb` вернул ненулевой код.
    """
    executable = adb_path if adb_path is not None else find_adb_executable()
    command = [str(executable)]
    if serial:
        command.extend(("-s", serial))
    command.extend(args)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            timeout=timeout,
            creationflags=_CREATE_NO_WINDOW,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise AdbError(f"adb команда зависла дольше {timeout}с: {' '.join(args)}") from exc
    except OSError as exc:
        raise AdbError(f"Не удалось запустить adb: {exc}") from exc

    command_result = AdbCommandResult(
        returncode=result.returncode,
        stdout=result.stdout.decode("utf-8", errors="replace").strip(),
        stderr=result.stderr.decode("utf-8", errors="replace").strip(),
    )
    if check and command_result.returncode != 0:
        details = command_result.stderr or command_result.stdout
        raise AdbError(f"adb вернул код {command_result.returncode}: {details}")

    return command_result
