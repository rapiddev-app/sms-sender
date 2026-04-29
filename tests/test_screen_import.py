"""Тесты чистых helper-функций экрана импорта."""

from core.models import ValidationError
from ui.screen_import import build_import_status, format_validation_error


def test_format_validation_error_uses_known_reason_label():
    error = ValidationError(
        row=3,
        raw_phone="123",
        raw_variable="Иван",
        reason="invalid_phone",
    )

    assert format_validation_error(error) == (
        "Строка 3: некорректный номер | номер: 123 | переменная: Иван"
    )


def test_format_validation_error_handles_empty_values():
    error = ValidationError(
        row=4,
        raw_phone="",
        raw_variable="",
        reason="empty_phone",
    )

    assert format_validation_error(error) == (
        "Строка 4: пустой номер | номер: пусто | переменная: пусто"
    )


def test_build_import_status_returns_default_without_file():
    assert build_import_status(has_file=False, contact_count=0, error_count=0) == (
        "Контактов: 0 | Ошибок: 0"
    )


def test_build_import_status_explains_empty_excel():
    assert build_import_status(has_file=True, contact_count=0, error_count=0) == (
        "В файле нет валидных контактов. Проверьте строки после заголовка."
    )


def test_build_import_status_explains_file_with_only_errors():
    assert build_import_status(has_file=True, contact_count=0, error_count=3) == (
        "Нет валидных контактов | Ошибок: 3"
    )
