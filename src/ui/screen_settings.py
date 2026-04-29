"""Экран настроек отправки и проверки подключения телефона."""

from collections.abc import Callable
from dataclasses import dataclass

import customtkinter as ctk

from adb.device_manager import ConnectionState, get_connection_status
from adb.sms_sender import is_companion_installed


@dataclass(frozen=True)
class SendSettingsDraft:
    """Черновик настроек отправки из UI."""

    group_size: int
    sms_delay_sec: float
    group_delay_sec: float


class SettingsScreen(ctk.CTkFrame):
    """Экран размера группы, задержек и статуса ADB."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        group_size: int,
        sms_delay_sec: float,
        group_delay_sec: float,
        on_settings_changed: Callable[[SendSettingsDraft], None],
        on_start: Callable[[], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._on_settings_changed = on_settings_changed
        self._on_start = on_start
        self._adb_ready = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_settings_panel(group_size, sms_delay_sec, group_delay_sec)
        self._build_phone_panel()
        self._update_start_state()

    def _build_settings_panel(
        self,
        group_size: int,
        sms_delay_sec: float,
        group_delay_sec: float,
    ) -> None:
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        panel.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="Параметры очереди",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 18), sticky="ew")

        self._group_size_entry = self._add_number_input(panel, 1, "Размер группы", group_size)
        self._sms_delay_entry = self._add_number_input(
            panel,
            2,
            "Задержка между SMS, сек",
            sms_delay_sec,
        )
        self._group_delay_entry = self._add_number_input(
            panel,
            3,
            "Задержка между группами, сек",
            group_delay_sec,
        )

        self._settings_error = ctk.CTkLabel(panel, text="", anchor="w", text_color="#ffb86c")
        self._settings_error.grid(row=4, column=0, columnspan=2, padx=16, pady=(10, 0), sticky="ew")

    def _add_number_input(
        self,
        master: ctk.CTkFrame,
        row: int,
        label_text: str,
        value: int | float,
    ) -> ctk.CTkEntry:
        label = ctk.CTkLabel(master, text=label_text, anchor="w")
        label.grid(row=row, column=0, padx=16, pady=8, sticky="ew")

        entry = ctk.CTkEntry(master)
        entry.insert(0, f"{value:g}")
        entry.grid(row=row, column=1, padx=16, pady=8, sticky="ew")
        entry.bind("<KeyRelease>", self._handle_settings_changed)
        return entry

    def _build_phone_panel(self) -> None:
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        panel.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="Телефон",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        self._phone_status = ctk.CTkLabel(
            panel,
            text="Статус не проверен",
            anchor="w",
            justify="left",
            wraplength=360,
        )
        self._phone_status.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")

        refresh_button = ctk.CTkButton(
            panel,
            text="Проверить ADB",
            command=self.refresh_adb_status,
        )
        refresh_button.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="ew")

        self._start_button = ctk.CTkButton(
            panel,
            text="Начать рассылку",
            command=self._on_start,
        )
        self._start_button.grid(row=3, column=0, padx=16, pady=(8, 16), sticky="ew")

    def refresh_adb_status(self) -> None:
        """Проверяет подключение телефона и наличие Android-компаньона."""
        status = get_connection_status()
        self._adb_ready = status.state == ConnectionState.READY

        message = status.message
        if self._adb_ready:
            try:
                companion_ready = is_companion_installed()
            except Exception as exc:  # noqa: BLE001 - статус должен попасть в UI.
                companion_ready = False
                message = f"{message}\nAndroid-компаньон: ошибка проверки ({exc})"
            else:
                if companion_ready:
                    message = f"{message}\nAndroid-компаньон установлен"
                else:
                    message = f"{message}\nAndroid-компаньон не установлен"
            self._adb_ready = self._adb_ready and companion_ready

        self._phone_status.configure(text=message)
        self._update_start_state()

    def _handle_settings_changed(self, event: object | None = None) -> None:
        try:
            draft = parse_settings(
                self._group_size_entry.get(),
                self._sms_delay_entry.get(),
                self._group_delay_entry.get(),
            )
        except ValueError as exc:
            self._settings_error.configure(text=str(exc))
        else:
            self._settings_error.configure(text="")
            self._on_settings_changed(draft)
        self._update_start_state()

    def _update_start_state(self) -> None:
        settings_ready = not self._settings_error.cget("text")
        state = "normal" if settings_ready and self._adb_ready else "disabled"
        self._start_button.configure(state=state)


def parse_settings(
    group_size_raw: str,
    sms_delay_raw: str,
    group_delay_raw: str,
) -> SendSettingsDraft:
    """Парсит и валидирует числовые настройки рассылки из UI."""
    try:
        group_size = int(group_size_raw)
    except ValueError as exc:
        raise ValueError("Размер группы должен быть целым числом") from exc

    try:
        sms_delay_sec = float(sms_delay_raw.replace(",", "."))
        group_delay_sec = float(group_delay_raw.replace(",", "."))
    except ValueError as exc:
        raise ValueError("Задержки должны быть числами") from exc

    if group_size <= 0:
        raise ValueError("Размер группы должен быть больше 0")
    if sms_delay_sec < 0:
        raise ValueError("Задержка между SMS не может быть отрицательной")
    if group_delay_sec < 0:
        raise ValueError("Задержка между группами не может быть отрицательной")

    return SendSettingsDraft(
        group_size=group_size,
        sms_delay_sec=sms_delay_sec,
        group_delay_sec=group_delay_sec,
    )
