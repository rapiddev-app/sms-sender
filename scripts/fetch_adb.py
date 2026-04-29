"""Скачивает Android Platform Tools и кладёт нужные файлы в `bin/adb/`.

Запуск:
    uv run scripts/fetch_adb.py

Скрипт идемпотентен: если все три файла уже на месте — ничего не делает.
Источник — официальный Google: dl.google.com/android/repository/platform-tools-latest-windows.zip
"""

import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

PLATFORM_TOOLS_URL = (
    "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
)
REQUIRED_FILES = ("adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGET_DIR = PROJECT_ROOT / "bin" / "adb"


def main() -> int:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    missing = [name for name in REQUIRED_FILES if not (TARGET_DIR / name).exists()]
    if not missing:
        print(f"[skip] Все файлы уже на месте: {TARGET_DIR}")
        return 0

    print(f"[info] Не хватает: {', '.join(missing)}")
    print(f"[info] Скачивание: {PLATFORM_TOOLS_URL}")

    with TemporaryDirectory() as tmp:
        archive_path = Path(tmp) / "platform-tools.zip"
        try:
            urllib.request.urlretrieve(PLATFORM_TOOLS_URL, archive_path)
        except OSError as exc:
            print(f"[error] Не удалось скачать: {exc}", file=sys.stderr)
            return 1

        print(f"[info] Распаковка → {TARGET_DIR}")
        with zipfile.ZipFile(archive_path) as zf:
            for member in zf.namelist():
                name = Path(member).name
                if name in REQUIRED_FILES:
                    with zf.open(member) as src, (TARGET_DIR / name).open("wb") as dst:
                        shutil.copyfileobj(src, dst)

    still_missing = [name for name in REQUIRED_FILES if not (TARGET_DIR / name).exists()]
    if still_missing:
        print(
            f"[error] После распаковки не найдены: {', '.join(still_missing)}",
            file=sys.stderr,
        )
        return 1

    print("[ok] Готово.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
