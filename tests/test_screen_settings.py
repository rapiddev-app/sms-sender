"""Тесты helper-функций экрана настроек."""

import pytest

from ui.screen_settings import SendSettingsDraft, parse_settings


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
