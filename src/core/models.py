"""Доменные модели для бизнес-логики (контакты, ошибки валидации, результат загрузки)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Contact:
    """Валидный контакт для рассылки SMS."""

    row: int
    """Номер строки в Excel (1-based, заголовок = 1)."""
    phone: str
    """Номер в нормализованном формате `+7xxxxxxxxxx`."""
    variable: str
    """Значение переменной для подстановки в шаблон сообщения."""


@dataclass(frozen=True)
class ValidationError:
    """Ошибка валидации строки Excel — попадает в отчёт пользователю."""

    row: int
    raw_phone: str
    raw_variable: str
    reason: str
    """Код причины: `empty_phone`, `invalid_phone`, `empty_variable`, `duplicate`."""


@dataclass(frozen=True)
class LoadResult:
    """Результат загрузки Excel-файла: валидные контакты + список ошибок."""

    contacts: list[Contact]
    errors: list[ValidationError]
