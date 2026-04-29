"""Сборка текста SMS из шаблона и подсчёт метрик для предпросмотра.

Модуль не зависит от GUI и ADB-слоя — это чистая бизнес-логика для Экрана 2.
"""

import math
from dataclasses import dataclass

PLACEHOLDER = "{переменная}"

GSM7_SINGLE_LIMIT = 160
GSM7_MULTIPART_LIMIT = 153
UCS2_SINGLE_LIMIT = 70
UCS2_MULTIPART_LIMIT = 67

ENCODING_GSM7 = "gsm7"
ENCODING_UCS2 = "ucs2"


@dataclass(frozen=True)
class SmsStats:
    """Метрики готового текста SMS для отображения в UI."""

    length: int
    """Длина текста в символах после подстановки переменной."""
    encoding: str
    """`gsm7` (только ASCII) либо `ucs2` (есть не-ASCII символы, в т.ч. кириллица)."""
    segments: int
    """Сколько SMS-сегментов потребуется для отправки."""
    per_segment_limit: int
    """Лимит символов на текущий сегмент — для индикатора `X / Y` в UI."""


def build_message(template: str, variable: str) -> str:
    """Подставляет значение переменной в шаблон по плейсхолдеру `{переменная}`.

    Если плейсхолдера в шаблоне нет — возвращает шаблон без изменений
    (решение об обязательности плейсхолдера принимает UI).
    """
    return template.replace(PLACEHOLDER, variable)


def count_sms(text: str) -> SmsStats:
    """Считает длину, кодировку и количество SMS-сегментов для текста."""
    encoding = _detect_encoding(text)
    length = len(text)

    if encoding == ENCODING_GSM7:
        single_limit = GSM7_SINGLE_LIMIT
        multipart_limit = GSM7_MULTIPART_LIMIT
    else:
        single_limit = UCS2_SINGLE_LIMIT
        multipart_limit = UCS2_MULTIPART_LIMIT

    if length <= single_limit:
        return SmsStats(
            length=length,
            encoding=encoding,
            segments=1,
            per_segment_limit=single_limit,
        )

    segments = math.ceil(length / multipart_limit)
    return SmsStats(
        length=length,
        encoding=encoding,
        segments=segments,
        per_segment_limit=multipart_limit,
    )


def _detect_encoding(text: str) -> str:
    # Упрощённая бинарная классификация: всё ASCII → GSM-7, иначе UCS-2.
    # Полную таблицу GSM-7 + extended escape в MVP не учитываем —
    # целевой кейс (русский язык) однозначно UCS-2.
    if all(ord(ch) < 128 for ch in text):
        return ENCODING_GSM7
    return ENCODING_UCS2
