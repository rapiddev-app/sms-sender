"""
Главный класс приложения.
Управляет окном и навигацией между экранами (wizard).
"""

import customtkinter as ctk


class SMSAutoApp:
    """Корневой класс приложения — инициализирует окно и тему."""

    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._root = ctk.CTk()
        self._root.title("Авто рассылка СМС")
        self._root.geometry("960x680")
        self._root.minsize(800, 600)
        # Центрируем окно при запуске
        self._root.after(0, self._center_window)

    def _center_window(self) -> None:
        """Размещает окно по центру экрана после инициализации."""
        self._root.update_idletasks()
        w = self._root.winfo_width()
        h = self._root.winfo_height()
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        self._root.geometry(f"{w}x{h}+{x}+{y}")

    def run(self) -> None:
        """Запускает главный цикл событий GUI."""
        self._root.mainloop()
