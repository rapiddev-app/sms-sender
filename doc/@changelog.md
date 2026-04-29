# Авто рассылка СМС - История изменений (Changelog)

## [2026-04-29] — Iteration 1 (in progress): Загрузчик Excel

### Добавлено
- `src/core/models.py` — dataclass-модели `Contact`, `ValidationError`, `LoadResult`
  (вынесены отдельно от загрузчика для переиспользования в `message_builder`,
  `send_queue`, UI-слое без риска циклических импортов)
- `src/core/excel_loader.py` — чтение `.xlsx` через openpyxl (read_only режим),
  нормализация номеров к формату `+7xxxxxxxxxx`, обнаружение дубликатов,
  пустых полей и невалидных строк. Системные ошибки бросают исключения
  (`FileNotFoundError`, `InvalidExcelFormatError`), доменные — попадают в
  `LoadResult.errors`
- `tests/conftest.py` — фабрика временных `.xlsx` через openpyxl
- `tests/test_excel_loader.py` — 24 unit-теста (happy path, валидация,
  дубликаты, нормализация, числовые значения из Excel, системные ошибки)
- `tests/fixtures/test_contacts.xlsx` — фикстура для ручной проверки
- В `.gitignore` добавлены: `.ruff_cache/`, `.pytest_cache/`, `.claude/`,
  `/test_contacts.xlsx` (корневая ad-hoc копия)

## [2026-04-29] — Iteration 0: Скелет проекта

### Добавлено
- Инициализация окружения через `uv`, `pyproject.toml` с зависимостями (`customtkinter`, `openpyxl`, `pytest`, `ruff`, `pyinstaller`)
- Физическая структура каталогов: `src/{ui,core,adb}/`, `tests/`, `bin/adb/`, `assets/`
- Точка входа `src/main.py` + класс `SMSAutoApp` в `src/app.py` — открывает пустое окно 960×680 с центровкой
- Конфигурация `ruff` в `pyproject.toml` (line-length 100, правила `E,F,W,I`)
- `README.md` с инструкцией по dev-запуску, тестам, линтеру и сборке `.exe`
