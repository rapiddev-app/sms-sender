# Авто рассылка СМС - История изменений (Changelog)

## [2026-04-29] — Iteration 0: Скелет проекта

### Добавлено
- Инициализация окружения через `uv`, `pyproject.toml` с зависимостями (`customtkinter`, `openpyxl`, `pytest`, `ruff`, `pyinstaller`)
- Физическая структура каталогов: `src/{ui,core,adb}/`, `tests/`, `bin/adb/`, `assets/`
- Точка входа `src/main.py` + класс `SMSAutoApp` в `src/app.py` — открывает пустое окно 960×680 с центровкой
- Конфигурация `ruff` в `pyproject.toml` (line-length 100, правила `E,F,W,I`)
- `README.md` с инструкцией по dev-запуску, тестам, линтеру и сборке `.exe`
