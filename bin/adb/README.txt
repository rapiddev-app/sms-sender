# ADB Platform Tools

Сюда нужны три файла Google Android Platform Tools:
  - adb.exe
  - AdbWinApi.dll
  - AdbWinUsbApi.dll

Эти файлы НЕ коммитятся в git (см. .gitignore).

## Как получить

Автоматически:
    uv run python scripts/fetch_adb.py

Вручную:
    1. Скачать https://developer.android.com/tools/releases/platform-tools
    2. Распаковать ZIP, скопировать три файла выше в эту папку.

Файлы включаются в .exe бандл через PyInstaller (см. build.py).
