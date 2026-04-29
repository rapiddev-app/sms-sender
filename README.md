# Авто рассылка СМС

Десктопный инструмент для массовой отправки персонализированных SMS через подключённый Android-телефон по USB.

## Требования

- Windows 10/11
- Android-телефон с включёнными **режимом разработчика** и **USB-отладкой**
- USB-кабель

> Python, ADB и другие утилиты **не нужны** — всё включено в `.exe`.

## Запуск (dev-режим)

### 1. Установить зависимости

```bash
uv sync
```

### 2. Положить ADB-бинарники

Скачать [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools) и распаковать `adb.exe`, `AdbWinApi.dll`, `AdbWinUsbApi.dll` в папку `bin/adb/`.

### 3. Запустить приложение

```bash
uv run python src/main.py
```

### 4. Прогнать тесты

```bash
uv run pytest
```

### 5. Проверить линтер

```bash
uv run ruff check src/
```

## Сборка .exe

```bash
uv run python build.py
```

Готовый файл появится в `dist/СМС Рассылка.exe`.

## Структура проекта

```
SMS auto/
├── src/
│   ├── main.py             # Точка входа
│   ├── app.py              # Главный класс, навигация между экранами
│   ├── ui/                 # GUI-экраны (wizard)
│   ├── core/               # Бизнес-логика (Excel, шаблоны, очередь)
│   └── adb/                # ADB-интеграция
├── tests/                  # Юнит-тесты (pytest)
├── bin/adb/                # adb.exe + DLL (не в git, добавить вручную)
├── assets/                 # Иконка приложения
├── doc/                    # Проектная документация
└── pyproject.toml          # Зависимости (uv)
```
