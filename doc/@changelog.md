# Авто рассылка СМС - История изменений (Changelog)

## [2026-04-29] — Iteration 2: Android-компаньон для отправки SMS

### Добавлено
- `android/sms_companion/` — минимальное Android-приложение-компаньон на Java:
  экран выдачи разрешения `SEND_SMS`, приём ADB-команд через broadcast,
  отправка SMS через `SmsManager`, фиксация статусов в JSONL-журнал
- `src/adb/companion.py` — общие ADB-утилиты для работы с Android-компаньоном
- `src/adb/sms_sender.py` — установка APK, открытие экрана разрешений,
  чтение auth token и отправка SMS-команд в Android-компаньон
- `src/adb/status_reader.py` — чтение статусов отправки из приватного журнала
  Android-компаньона через `adb exec-out run-as`
- `tests/test_sms_sender.py`, `tests/test_status_reader.py` — unit-тесты ADB-клиента
  без реального запуска `adb.exe`
- CLI-команда `sms-auto-install-companion` для установки APK и открытия экрана
  выдачи разрешений
- ADR-0004: собственный Android-компаньон вместо автоматизации чужого SMS-приложения

### Изменено
- План Iteration 2 переведён с `ACTION_SENDTO` на контролируемую отправку через
  Android-компаньон
- Android-сборка зафиксирована на совместимой паре AGP `8.12.0` + Gradle `8.13`

## [2026-04-29] — Iteration 2 (in progress): ADB device_manager

### Добавлено
- `src/adb/device_manager.py` — поиск подключённых Android-устройств через
  `subprocess` + системный `adb.exe`. Публичные API: `find_adb_executable`,
  `list_devices`, `get_connection_status`. Парсер `_parse_devices_output`
  устойчив к шумным строкам adb-демона и метаданным `-l`. Все ошибки
  оборачиваются в `AdbNotFoundError` / `AdbError`, высокоуровневая функция
  `get_connection_status` агрегирует их в 7 состояний для GUI
  (`READY`, `NO_DEVICE`, `UNAUTHORIZED`, `OFFLINE`, `MULTIPLE_DEVICES`,
  `ADB_NOT_FOUND`, `ADB_ERROR`)
- `tests/test_device_manager.py` — 22 unit-теста: парсер вывода, обёртка
  subprocess (моки timeout/exit code/OSError), агрегатор статусов, поиск
  `adb.exe` (через подмену `_PROJECT_ROOT` и `sys._MEIPASS`)
- ADR-0003: прямой вызов `adb.exe` вместо `pure-python-adb`

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
