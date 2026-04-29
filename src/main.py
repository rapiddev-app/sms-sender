"""
Точка входа приложения.
Запускается как `python src/main.py` в dev-режиме
или как собранный `.exe` через PyInstaller.
"""

import os
import sys

# Добавляем src/ в путь поиска модулей для корректного импорта при запуске через python src/main.py
sys.path.insert(0, os.path.dirname(__file__))

from app import SMSAutoApp


def main() -> None:
    app = SMSAutoApp()
    app.run()


if __name__ == "__main__":
    main()
