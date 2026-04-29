"""Тесты helper-функций конструктора шаблона."""

from ui.screen_builder import build_template_error, is_template_ready


def test_is_template_ready_returns_true_for_non_empty_template():
    assert is_template_ready("Привет, {переменная}") is True


def test_is_template_ready_returns_false_for_blank_template():
    assert is_template_ready("  \n  ") is False


def test_build_template_error_returns_empty_string_for_valid_template():
    assert build_template_error("Привет") == ""


def test_build_template_error_explains_blank_template():
    assert build_template_error("  \n  ") == "Введите текст SMS-шаблона"
