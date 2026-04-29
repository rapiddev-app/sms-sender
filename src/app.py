"""
Главный класс приложения.
Управляет окном и навигацией между экранами (wizard).
"""

import sys
import tkinter as tk
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import customtkinter as ctk

from core.models import Contact, ValidationError
from core.send_queue import SendQueueSettings
from core.template_store import SavedTemplate, TemplateStore, TemplateStoreError
from ui.screen_builder import BuilderScreen, is_template_ready
from ui.screen_import import ImportScreen
from ui.screen_sending import SendingScreen
from ui.screen_settings import SendSettingsDraft, SettingsScreen


class WizardStep(Enum):
    """Шаги wizard-интерфейса."""

    IMPORT = 0
    BUILDER = 1
    SETTINGS = 2
    SENDING = 3


@dataclass
class WizardState:
    """Состояние, которое передаётся между экранами wizard."""

    excel_path: Path | None = None
    contacts: list[Contact] = field(default_factory=list)
    validation_errors: list[ValidationError] = field(default_factory=list)
    template: str = ""
    group_size: int = 10
    sms_delay_sec: float = 3.0
    group_delay_sec: float = 60.0
    saved_templates: list[SavedTemplate] = field(default_factory=list)


_STEP_ORDER = [
    WizardStep.IMPORT,
    WizardStep.BUILDER,
    WizardStep.SETTINGS,
    WizardStep.SENDING,
]

_STEP_TITLES = {
    WizardStep.IMPORT: "Загрузка базы",
    WizardStep.BUILDER: "Шаблон SMS",
    WizardStep.SETTINGS: "Настройки",
    WizardStep.SENDING: "Рассылка",
}

_STEP_SUBTITLES = {
    WizardStep.IMPORT: "Импорт контактов и проверка номеров",
    WizardStep.BUILDER: "Текст сообщения и персональная переменная",
    WizardStep.SETTINGS: "Группы, задержки и подключение телефона",
    WizardStep.SENDING: "Прогресс, статусы и управление очередью",
}

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ASSETS_DIR_NAME = "assets"
_APP_ICON_FILENAME = "icon.ico"


def _asset_path(filename: str) -> Path:
    """Возвращает путь к bundled-ресурсу в PyInstaller или к dev-файлу проекта."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root is not None:
        return Path(bundle_root) / _ASSETS_DIR_NAME / filename
    return _PROJECT_ROOT / _ASSETS_DIR_NAME / filename


class SMSAutoApp:
    """Корневой класс приложения — инициализирует окно, тему и wizard-навигацию."""

    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._state = WizardState()
        self._template_store = TemplateStore()
        try:
            self._state.saved_templates = self._template_store.load_templates()
        except TemplateStoreError:
            self._state.saved_templates = []
        self._current_step = WizardStep.IMPORT
        self._sending_started = False
        self._sending_paused = False
        self._sending_completed = False
        self._sending_screen_frame: ctk.CTkFrame | None = None
        self._sending_screen: SendingScreen | None = None
        self._step_buttons: dict[WizardStep, ctk.CTkButton] = {}
        self._screen_frame: ctk.CTkFrame | None = None

        self._root = ctk.CTk()
        self._root.title("Авто рассылка СМС")
        self._set_window_icon()
        self._root.geometry("960x680")
        self._root.minsize(800, 600)
        self._root.grid_columnconfigure(0, weight=1)
        self._root.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_screen_host()
        self._build_footer()
        self.show_step(WizardStep.IMPORT)

        # Центрируем окно при запуске
        self._root.after(0, self._center_window)

    def _set_window_icon(self) -> None:
        """Устанавливает иконку окна, если ресурс доступен и принят Tk."""
        icon_path = _asset_path(_APP_ICON_FILENAME)
        if not icon_path.is_file():
            return
        try:
            self._root.iconbitmap(str(icon_path))
        except tk.TclError:
            return

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

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self._root, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(tuple(range(len(_STEP_ORDER))), weight=1)

        for index, step in enumerate(_STEP_ORDER, start=1):
            button = ctk.CTkButton(
                header,
                text=f"{index}. {_STEP_TITLES[step]}",
                command=lambda selected_step=step: self.show_step(selected_step),
                height=40,
            )
            button.grid(row=0, column=index - 1, padx=8, pady=12, sticky="ew")
            self._step_buttons[step] = button

    def _build_screen_host(self) -> None:
        self._content = ctk.CTkFrame(self._root, corner_radius=0)
        self._content.grid(row=1, column=0, padx=24, pady=(18, 12), sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self._root, corner_radius=0)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        self._back_button = ctk.CTkButton(
            footer,
            text="Назад",
            command=self.go_back,
            width=140,
        )
        self._back_button.grid(row=0, column=1, padx=(24, 8), pady=14)

        self._next_button = ctk.CTkButton(
            footer,
            text="Далее",
            command=self.go_next,
            width=140,
        )
        self._next_button.grid(row=0, column=2, padx=(8, 24), pady=14)

    def go_next(self) -> None:
        """Переходит к следующему шагу, если он существует."""
        if self._current_step == WizardStep.IMPORT and not self._state.contacts:
            return
        if self._current_step == WizardStep.BUILDER and not is_template_ready(
            self._state.template
        ):
            return
        current_index = _STEP_ORDER.index(self._current_step)
        if current_index >= len(_STEP_ORDER) - 1:
            return
        self.show_step(_STEP_ORDER[current_index + 1])

    def go_back(self) -> None:
        """Переходит к предыдущему шагу, если он существует."""
        if self._current_step == WizardStep.SENDING and self._sending_paused:
            self.show_step(WizardStep.BUILDER)
            return
        current_index = _STEP_ORDER.index(self._current_step)
        if current_index <= 0:
            return
        self.show_step(_STEP_ORDER[current_index - 1])

    def show_step(self, step: WizardStep) -> None:
        """Отображает выбранный шаг wizard."""
        if step == self._current_step and self._screen_frame is not None:
            return
        if step == WizardStep.SENDING and not self._sending_started:
            return
        if (
            self._current_step == WizardStep.SENDING
            and step != WizardStep.SENDING
            and not self._sending_paused
            and not self._sending_completed
        ):
            return
        self._current_step = step
        self._render_current_screen()
        self._update_navigation_state()

    def _render_current_screen(self) -> None:
        if self._screen_frame is not None:
            if self._screen_frame is self._sending_screen_frame:
                self._screen_frame.grid_forget()
            else:
                self._screen_frame.destroy()

        if self._current_step == WizardStep.SENDING and self._sending_screen_frame is not None:
            self._screen_frame = self._sending_screen_frame
            self._screen_frame.grid(row=0, column=0, sticky="nsew")
            return

        self._screen_frame = ctk.CTkFrame(self._content, corner_radius=8)
        self._screen_frame.grid(row=0, column=0, sticky="nsew")
        self._screen_frame.grid_columnconfigure(0, weight=1)
        self._screen_frame.grid_rowconfigure(2, weight=1)

        step_number = _STEP_ORDER.index(self._current_step) + 1
        title = ctk.CTkLabel(
            self._screen_frame,
            text=f"{step_number}. {_STEP_TITLES[self._current_step]}",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, padx=28, pady=(28, 6), sticky="ew")

        subtitle = ctk.CTkLabel(
            self._screen_frame,
            text=_STEP_SUBTITLES[self._current_step],
            font=ctk.CTkFont(size=14),
            anchor="w",
            text_color=("gray35", "gray70"),
        )
        subtitle.grid(row=1, column=0, padx=28, pady=(0, 20), sticky="ew")

        body = ctk.CTkFrame(self._screen_frame, fg_color="transparent")
        body.grid(row=2, column=0, padx=28, pady=(0, 28), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        if self._current_step == WizardStep.IMPORT:
            self._render_import_screen(body)
            return
        if self._current_step == WizardStep.BUILDER:
            self._render_builder_screen(body)
            return
        if self._current_step == WizardStep.SETTINGS:
            self._render_settings_screen(body)
            return
        if self._current_step == WizardStep.SENDING:
            self._render_sending_screen(body)
            return

        state_label = ctk.CTkLabel(
            body,
            text=self._build_state_summary(),
            justify="left",
            anchor="nw",
            font=ctk.CTkFont(size=15),
        )
        state_label.grid(row=0, column=0, sticky="nsew")

    def _render_import_screen(self, master: ctk.CTkFrame) -> None:
        screen = ImportScreen(
            master,
            excel_path=self._state.excel_path,
            contacts=self._state.contacts,
            validation_errors=self._state.validation_errors,
            on_loaded=self._handle_import_loaded,
        )
        screen.grid(row=0, column=0, sticky="nsew")

    def _render_settings_screen(self, master: ctk.CTkFrame) -> None:
        screen = SettingsScreen(
            master,
            group_size=self._state.group_size,
            sms_delay_sec=self._state.sms_delay_sec,
            group_delay_sec=self._state.group_delay_sec,
            on_settings_changed=self._handle_settings_changed,
            on_start=self._start_sending,
        )
        screen.grid(row=0, column=0, sticky="nsew")

    def _start_sending(self) -> None:
        self._sending_started = True
        self._sending_paused = False
        self._sending_completed = False
        self.show_step(WizardStep.SENDING)

    def _render_sending_screen(self, master: ctk.CTkFrame) -> None:
        screen = SendingScreen(
            master,
            contacts=self._state.contacts,
            source_excel_path=self._state.excel_path,
            template=self._state.template,
            settings=SendQueueSettings(
                group_size=self._state.group_size,
                sms_delay_sec=self._state.sms_delay_sec,
                group_delay_sec=self._state.group_delay_sec,
            ),
            on_paused=self._handle_sending_paused,
            on_resumed=self._handle_sending_resumed,
            on_stopped=self._handle_sending_completed,
            on_finished=self._handle_sending_completed,
        )
        self._sending_screen_frame = self._screen_frame
        self._sending_screen = screen
        screen.grid(row=0, column=0, sticky="nsew")

    def _render_builder_screen(self, master: ctk.CTkFrame) -> None:
        screen = BuilderScreen(
            master,
            contacts=self._state.contacts,
            template=self._state.template,
            templates=self._state.saved_templates,
            on_template_changed=self._handle_template_changed,
            on_save_template=self._handle_save_template,
            on_delete_template=self._handle_delete_template,
        )
        screen.grid(row=0, column=0, sticky="nsew")

    def _handle_import_loaded(
        self,
        excel_path: Path,
        contacts: list[Contact],
        validation_errors: list[ValidationError],
    ) -> None:
        self._state.excel_path = excel_path
        self._state.contacts = contacts
        self._state.validation_errors = validation_errors
        self._update_navigation_state()

    def _handle_template_changed(self, template: str) -> None:
        self._state.template = template
        if self._sending_screen is not None:
            self._sending_screen.update_template(template)
        self._update_navigation_state()

    def _handle_save_template(self, name: str, text: str) -> list[SavedTemplate]:
        self._state.saved_templates = self._template_store.save_template(name, text)
        return self._state.saved_templates

    def _handle_delete_template(self, name: str) -> list[SavedTemplate]:
        self._state.saved_templates = self._template_store.delete_template(name)
        return self._state.saved_templates

    def _handle_settings_changed(self, settings: SendSettingsDraft) -> None:
        self._state.group_size = settings.group_size
        self._state.sms_delay_sec = settings.sms_delay_sec
        self._state.group_delay_sec = settings.group_delay_sec

    def _handle_sending_paused(self) -> None:
        self._sending_paused = True
        self._update_navigation_state()

    def _handle_sending_resumed(self) -> None:
        self._sending_paused = False
        self._current_step = WizardStep.SENDING
        self._update_navigation_state()

    def _handle_sending_completed(self) -> None:
        self._sending_paused = False
        self._sending_completed = True
        self._update_navigation_state()

    def _build_state_summary(self) -> str:
        excel_name = self._state.excel_path.name if self._state.excel_path else "не выбран"
        return (
            f"Файл: {excel_name}\n"
            f"Контактов: {len(self._state.contacts)}\n"
            f"Ошибок импорта: {len(self._state.validation_errors)}\n"
            f"Шаблон: {'задан' if self._state.template else 'не задан'}\n"
            f"Группа: {self._state.group_size}\n"
            f"Задержка SMS: {self._state.sms_delay_sec:g} сек\n"
            f"Задержка группы: {self._state.group_delay_sec:g} сек"
        )

    def _update_navigation_state(self) -> None:
        current_index = _STEP_ORDER.index(self._current_step)
        if self._current_step == WizardStep.SENDING:
            self._back_button.configure(state="normal" if self._sending_paused else "disabled")
            self._next_button.configure(state="disabled")
            for step, button in self._step_buttons.items():
                if step == self._current_step:
                    button.configure(
                        state="normal" if self._sending_paused else "disabled",
                        fg_color=("#1f6aa5", "#1f6aa5"),
                    )
                elif self._sending_paused and step == WizardStep.BUILDER:
                    button.configure(state="normal", fg_color=("gray75", "gray25"))
                else:
                    button.configure(state="disabled", fg_color=("gray75", "gray25"))
            return

        self._back_button.configure(state="normal" if current_index > 0 else "disabled")
        next_enabled = current_index < len(_STEP_ORDER) - 1
        if self._current_step == WizardStep.IMPORT and not self._state.contacts:
            next_enabled = False
        if self._current_step == WizardStep.BUILDER and not is_template_ready(
            self._state.template
        ):
            next_enabled = False
        self._next_button.configure(state="normal" if next_enabled else "disabled")

        for step, button in self._step_buttons.items():
            if step == self._current_step:
                button.configure(state="normal", fg_color=("#1f6aa5", "#1f6aa5"))
            elif step == WizardStep.SENDING:
                state = "normal" if self._sending_paused else "disabled"
                button.configure(state=state, fg_color=("gray75", "gray25"))
            else:
                button.configure(state="normal", fg_color=("gray75", "gray25"))

    def run(self) -> None:
        """Запускает главный цикл событий GUI."""
        self._root.mainloop()
