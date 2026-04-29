"""Команды отправки SMS через Android-приложение-компаньон."""

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from adb.companion import (
    COMPANION_ACTION_SEND_SMS,
    COMPANION_COMMAND_RECEIVER,
    COMPANION_MAIN_ACTIVITY,
    COMPANION_PACKAGE,
    AdbCommandResult,
    find_companion_apk,
    run_adb,
)
from adb.device_manager import AdbError

_AUTH_TOKEN_PATH = "files/adb_token.txt"


@dataclass(frozen=True)
class SmsCommandResult:
    """Результат передачи команды отправки Android-компаньону."""

    request_id: str
    adb_result: AdbCommandResult


def is_companion_installed(adb_path: Path | None = None, serial: str | None = None) -> bool:
    """Проверяет, установлен ли Android-компаньон на подключённом устройстве."""
    result = run_adb(
        ["shell", "pm", "path", COMPANION_PACKAGE],
        adb_path=adb_path,
        serial=serial,
        check=False,
    )
    return result.returncode == 0 and result.stdout.startswith("package:")


def install_companion(
    apk_path: Path | None = None,
    *,
    adb_path: Path | None = None,
    serial: str | None = None,
) -> AdbCommandResult:
    """Устанавливает debug APK Android-компаньона через `adb install -r`."""
    resolved_apk = apk_path if apk_path is not None else find_companion_apk()
    if not resolved_apk.exists():
        raise AdbError(
            f"APK Android-компаньона не найден: {resolved_apk}. "
            "Сначала соберите `android/sms_companion`."
        )

    return run_adb(
        ["install", "-r", str(resolved_apk)],
        adb_path=adb_path,
        serial=serial,
        timeout=60,
    )


def open_permission_screen(
    adb_path: Path | None = None,
    serial: str | None = None,
) -> AdbCommandResult:
    """Открывает экран Android-компаньона для выдачи разрешения `SEND_SMS`."""
    return run_adb(
        ["shell", "am", "start", "-n", COMPANION_MAIN_ACTIVITY],
        adb_path=adb_path,
        serial=serial,
    )


def install_and_open_companion() -> None:
    """CLI helper: установить Android-компаньон и открыть экран разрешений."""
    install_companion()
    open_permission_screen()
    print("APK установлен, выдайте SEND_SMS на телефоне")


def read_auth_token(adb_path: Path | None = None, serial: str | None = None) -> str:
    """Читает приватный токен компаньона для авторизации ADB-команд."""
    result = run_adb(
        ["exec-out", "run-as", COMPANION_PACKAGE, "cat", _AUTH_TOKEN_PATH],
        adb_path=adb_path,
        serial=serial,
    )
    token = result.stdout.strip()
    if not token:
        raise AdbError(
            "Android-компаньон не вернул auth token. "
            "Откройте экран разрешений компаньона и повторите попытку."
        )
    return token


def send_sms(
    phone: str,
    message: str,
    *,
    request_id: str | None = None,
    auth_token: str | None = None,
    adb_path: Path | None = None,
    serial: str | None = None,
) -> SmsCommandResult:
    """Передаёт Android-компаньону команду отправить SMS."""
    normalized_phone = phone.strip()
    if not normalized_phone:
        raise ValueError("phone не должен быть пустым")
    if not message:
        raise ValueError("message не должен быть пустым")

    resolved_request_id = request_id or uuid4().hex
    resolved_auth_token = auth_token or read_auth_token(adb_path=adb_path, serial=serial)

    result = run_adb(
        [
            "shell",
            "am",
            "broadcast",
            "-a",
            COMPANION_ACTION_SEND_SMS,
            "-n",
            COMPANION_COMMAND_RECEIVER,
            "--es",
            "auth_token",
            resolved_auth_token,
            "--es",
            "request_id",
            resolved_request_id,
            "--es",
            "phone",
            normalized_phone,
            "--es",
            "message",
            message,
        ],
        adb_path=adb_path,
        serial=serial,
    )

    return SmsCommandResult(request_id=resolved_request_id, adb_result=result)
