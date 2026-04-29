"""Тесты helper-функций конструктора шаблона."""

from ui.screen_builder import is_template_ready


def test_is_template_ready_returns_true_for_non_empty_template():
    assert is_template_ready("Привет, {переменная}") is True


def test_is_template_ready_returns_false_for_blank_template():
    assert is_template_ready("  \n  ") is False
