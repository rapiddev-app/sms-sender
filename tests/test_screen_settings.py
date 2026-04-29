"""Тесты helper-функций экрана настроек."""

import pytest

from adb.device_manager import ConnectionState, ConnectionStatus
from ui import screen_settings
from ui.screen_settings import (
    PhoneCheckResult,
    SendSettingsDraft,
    check_phone_ready,
    parse_settings,
)


def test_parse_settings_returns_draft_for_valid_values():
    assert parse_settings("10", "3.5", "60") == SendSettingsDraft(
        group_size=10,
        sms_delay_sec=3.5,
        group_delay_sec=60.0,
    )


def test_parse_settings_accepts_comma_decimal_separator():
    assert parse_settings("5", "1,5", "30,25") == SendSettingsDraft(
        group_size=5,
        sms_delay_sec=1.5,
        group_delay_sec=30.25,
    )


def test_parse_settings_rejects_non_integer_group_size():
    with pytest.raises(ValueError, match="целым"):
        parse_settings("1.5", "1", "10")


def test_parse_settings_rejects_negative_delay():
    with pytest.raises(ValueError, match="не может быть отрицательной"):
        parse_settings("10", "-1", "10")


def test_check_phone_ready_returns_not_ready_when_device_missing(monkeypatch):
    monkeypatch.setattr(
        screen_settings,
        "get_connection_status",
        lambda: ConnectionStatus(
            state=ConnectionState.NO_DEVICE,
            message="Телефон не обнаружен",
        ),
    )

    assert check_phone_ready() == PhoneCheckResult(
        ready=False,
        message="Телефон не обнаружен",
    )


def test_check_phone_ready_returns_ready_when_companion_installed(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        screen_settings,
        "get_connection_status",
        lambda: ConnectionStatus(state=ConnectionState.READY, message="Устройство подключено"),
    )
    monkeypatch.setattr(screen_settings, "is_companion_installed", lambda: True)
    monkeypatch.setattr(screen_settings, "install_companion", lambda: calls.append("install"))

    assert check_phone_ready() == PhoneCheckResult(
        ready=True,
        message="Устройство подключено\nAndroid-компаньон установлен и обновлён",
    )
    assert calls == ["install"]


def test_check_phone_ready_installs_missing_companion_and_opens_permissions(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        screen_settings,
        "get_connection_status",
        lambda: ConnectionStatus(state=ConnectionState.READY, message="Устройство подключено"),
    )
    monkeypatch.setattr(screen_settings, "is_companion_installed", lambda: False)
    monkeypatch.setattr(screen_settings, "install_companion", lambda: calls.append("install"))
    monkeypatch.setattr(screen_settings, "open_permission_screen", lambda: calls.append("open"))

    result = check_phone_ready()

    assert calls == ["install", "open"]
    assert result.ready is False
    assert "Выдайте разрешение SEND_SMS" in result.message


def test_check_phone_ready_reports_install_error(monkeypatch):
    monkeypatch.setattr(
        screen_settings,
        "get_connection_status",
        lambda: ConnectionStatus(state=ConnectionState.READY, message="Устройство подключено"),
    )
    monkeypatch.setattr(screen_settings, "is_companion_installed", lambda: False)

    def raise_install_error() -> None:
        raise RuntimeError("apk missing")

    monkeypatch.setattr(screen_settings, "install_companion", raise_install_error)

    result = check_phone_ready()

    assert result.ready is False
    assert "apk missing" in result.message
