"""Чтение статусов отправки из Android-приложения-компаньона."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adb.companion import COMPANION_PACKAGE, run_adb
from adb.device_manager import AdbError

_STATUS_LOG_PATH = "files/statuses.jsonl"


@dataclass(frozen=True)
class SmsStatus:
    """Одна запись статуса SMS из журнала Android-компаньона."""

    request_id: str
    phone: str
    state: str
    details: str
    timestamp_ms: int


def read_statuses(adb_path: Path | None = None, serial: str | None = None) -> list[SmsStatus]:
    """Возвращает список статусов из приватного JSONL-журнала компаньона."""
    result = run_adb(
        ["exec-out", "run-as", COMPANION_PACKAGE, "cat", _STATUS_LOG_PATH],
        adb_path=adb_path,
        serial=serial,
        check=False,
    )
    if result.returncode != 0:
        missing_file = "No such file" in result.stderr or "No such file" in result.stdout
        if missing_file:
            return []
        details = result.stderr or result.stdout
        raise AdbError(f"Не удалось прочитать статусы Android-компаньона: {details}")

    statuses: list[SmsStatus] = []
    for line in result.stdout.splitlines():
        parsed = _parse_status_line(line)
        if parsed is not None:
            statuses.append(parsed)
    return statuses


def _parse_status_line(line: str) -> SmsStatus | None:
    """Парсит одну JSONL-строку; битые строки игнорируются."""
    if not line.strip():
        return None

    try:
        payload: dict[str, Any] = json.loads(line)
        return SmsStatus(
            request_id=str(payload["request_id"]),
            phone=str(payload["phone"]),
            state=str(payload["state"]),
            details=str(payload.get("details", "")),
            timestamp_ms=int(payload["timestamp_ms"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
