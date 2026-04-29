# Конвенции кода: Авто рассылка СМС

## Язык и фреймворк
Python 3.11+ / CustomTkinter

---

## Naming

| Сущность | Стиль | Пример |
|---|---|---|
| Переменные, функции | `snake_case` | `phone_number`, `load_excel()` |
| Классы | `PascalCase` | `ExcelLoader`, `SmsSender` |
| Константы | `UPPER_SNAKE_CASE` | `MAX_SMS_LENGTH = 160` |
| Файлы и модули | `snake_case` | `excel_loader.py`, `sms_sender.py` |
| Приватные методы | `_leading_underscore` | `_validate_phone()` |

---

## Стиль кода

- **Линтер + форматтер:** `ruff` (единый инструмент вместо flake8 + black)
- **Максимальная длина строки:** 100 символов
- **Кавычки:** двойные `"`
- **Типизация:** обязательны аннотации типов для всех публичных функций

```python
# Правильно
def build_message(template: str, variable: str) -> str:
    return template.replace("{переменная}", variable)

# Неправильно (нет аннотаций)
def build_message(template, variable):
    return template.replace("{переменная}", variable)
```

- **Docstring:** для публичных классов и функций с неочевидной сигнатурой
- **Комментарии:** объясняй «почему», а не «что»

---

## Конфигурация ruff

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I"]  # pycodestyle + pyflakes + isort
```

---

## Тестирование

- **Фреймворк:** `pytest`
- **Покрытие:** только `src/core/` (бизнес-логика)
- **Naming тестов:** `test_<что_тестируем>_<ожидаемый_результат>`

```python
# Примеры
def test_validate_phone_returns_true_for_valid_number(): ...
def test_validate_phone_returns_false_for_short_number(): ...
def test_build_message_inserts_variable_correctly(): ...
```

- **Расположение тестов:** `tests/` с зеркальной структурой относительно `src/core/`

---

## Git

- **Формат коммитов:** [Conventional Commits](https://www.conventionalcommits.org/)
- **Язык коммитов:** русский

```
feat(ui): добавить экран загрузки Excel
fix(adb): исправить определение подключённого устройства
refactor(core): вынести валидацию номеров в отдельный модуль
chore(deps): обновить зависимости через uv
```

- **Ветки:**

| Ветка | Назначение |
|---|---|
| `main` | Стабильная версия (production-ready) |
| `feat/*` | Новая функциональность |
| `fix/*` | Исправление багов |

---

## Структура импортов

Порядок блоков импортов (ruff/isort):
1. Стандартная библиотека Python
2. Сторонние пакеты
3. Внутренние модули проекта

```python
import os
import threading

import customtkinter as ctk
import openpyxl

from core.excel_loader import ExcelLoader
from adb.sms_sender import SmsSender
```
