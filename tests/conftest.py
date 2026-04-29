"""Общие фикстуры для тестов."""

from pathlib import Path
from typing import Any

import pytest
from openpyxl import Workbook


@pytest.fixture
def make_xlsx(tmp_path: Path):
    """Фабрика временных `.xlsx`-файлов для тестов excel_loader.

    Первая строка всегда заголовок (`Телефон`, `Имя`).
    Передаваемые `rows` записываются начиная со второй строки.
    """

    def _make(rows: list[tuple[Any, ...]], filename: str = "test.xlsx") -> Path:
        path = tmp_path / filename
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(("Телефон", "Имя"))
        for row in rows:
            worksheet.append(row)
        workbook.save(path)
        return path

    return _make
