"""Тесты загрузчика Excel и нормализатора номеров."""

from pathlib import Path

import pytest

from core.excel_loader import (
    InvalidExcelFormatError,
    load_excel,
    normalize_phone,
)


class TestNormalizePhone:
    def test_normalize_phone_10_digits_returns_plus7_format(self):
        assert normalize_phone("9991234567") == "+79991234567"

    def test_normalize_phone_with_8_prefix_returns_plus7_format(self):
        assert normalize_phone("89991234567") == "+79991234567"

    def test_normalize_phone_with_7_prefix_returns_plus7_format(self):
        assert normalize_phone("79991234567") == "+79991234567"

    def test_normalize_phone_keeps_plus7_format(self):
        assert normalize_phone("+79991234567") == "+79991234567"

    def test_normalize_phone_strips_spaces_dashes_parens(self):
        assert normalize_phone("+7 (999) 123-45-67") == "+79991234567"
        assert normalize_phone("8 (999) 123 45 67") == "+79991234567"

    def test_normalize_phone_accepts_int_input(self):
        assert normalize_phone(89991234567) == "+79991234567"

    def test_normalize_phone_accepts_float_input(self):
        assert normalize_phone(89991234567.0) == "+79991234567"

    def test_normalize_phone_returns_none_for_landline(self):
        # 4-я цифра не 9 — городской/немобильный
        assert normalize_phone("84951234567") is None

    def test_normalize_phone_returns_none_for_short_number(self):
        assert normalize_phone("12345") is None

    def test_normalize_phone_returns_none_for_none(self):
        assert normalize_phone(None) is None

    def test_normalize_phone_returns_none_for_empty_string(self):
        assert normalize_phone("") is None

    def test_normalize_phone_returns_none_for_garbage(self):
        assert normalize_phone("abcd") is None
        assert normalize_phone("+++") is None

    def test_normalize_phone_returns_none_for_non_integer_float(self):
        assert normalize_phone(1.5) is None


class TestLoadExcelHappyPath:
    def test_load_excel_returns_valid_contacts(self, make_xlsx):
        path = make_xlsx(
            [
                ("9991234567", "Иван"),
                ("89997654321", "Мария"),
                ("+79993334455", "Пётр"),
            ]
        )
        result = load_excel(path)

        assert result.errors == []
        assert len(result.contacts) == 3
        assert result.contacts[0].phone == "+79991234567"
        assert result.contacts[0].variable == "Иван"
        assert result.contacts[0].row == 2
        assert result.contacts[1].phone == "+79997654321"
        assert result.contacts[2].phone == "+79993334455"

    def test_load_excel_skips_header_row(self, make_xlsx):
        path = make_xlsx([("9991234567", "Иван")])
        result = load_excel(path)
        assert result.contacts[0].row == 2

    def test_load_excel_handles_numeric_phone_from_excel(self, make_xlsx):
        path = make_xlsx([(89991234567, "Иван")])
        result = load_excel(path)
        assert len(result.contacts) == 1
        assert result.contacts[0].phone == "+79991234567"

    def test_load_excel_skips_trailing_empty_rows(self, make_xlsx):
        path = make_xlsx(
            [
                ("9991234567", "Иван"),
                (None, None),
                (None, None),
            ]
        )
        result = load_excel(path)
        assert len(result.contacts) == 1
        assert result.errors == []

    def test_load_excel_strips_whitespace_in_variable(self, make_xlsx):
        path = make_xlsx([("9991234567", "  Иван  ")])
        result = load_excel(path)
        assert result.contacts[0].variable == "Иван"


class TestLoadExcelValidationErrors:
    def test_load_excel_reports_invalid_phone(self, make_xlsx):
        path = make_xlsx(
            [
                ("9991234567", "Иван"),
                ("12345", "Битый"),
            ]
        )
        result = load_excel(path)

        assert len(result.contacts) == 1
        assert len(result.errors) == 1
        assert result.errors[0].reason == "invalid_phone"
        assert result.errors[0].row == 3
        assert result.errors[0].raw_phone == "12345"

    def test_load_excel_reports_empty_phone(self, make_xlsx):
        path = make_xlsx([(None, "Без номера")])
        result = load_excel(path)

        assert len(result.errors) == 1
        assert result.errors[0].reason == "empty_phone"
        assert result.errors[0].raw_variable == "Без номера"

    def test_load_excel_reports_empty_variable(self, make_xlsx):
        path = make_xlsx([("9991234567", None)])
        result = load_excel(path)

        assert len(result.errors) == 1
        assert result.errors[0].reason == "empty_variable"

    def test_load_excel_reports_duplicate_after_normalization(self, make_xlsx):
        path = make_xlsx(
            [
                ("9991234567", "Иван"),
                ("89991234567", "Дубль"),  # тот же номер после нормализации
            ]
        )
        result = load_excel(path)

        assert len(result.contacts) == 1
        assert len(result.errors) == 1
        assert result.errors[0].reason == "duplicate"
        assert result.errors[0].row == 3


class TestLoadExcelSystemErrors:
    def test_load_excel_raises_for_missing_file(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_excel(tmp_path / "no_such_file.xlsx")

    def test_load_excel_raises_for_corrupt_format(self, tmp_path: Path):
        path = tmp_path / "broken.xlsx"
        path.write_bytes(b"not a real xlsx")

        with pytest.raises(InvalidExcelFormatError):
            load_excel(path)
