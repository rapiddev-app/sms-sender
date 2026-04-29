"""Экран импорта Excel-файла с контактами."""

from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from core.excel_loader import InvalidExcelFormatError, load_excel
from core.models import Contact, ValidationError

MAX_PREVIEW_ROWS = 12

_ERROR_LABELS = {
    "empty_phone": "пустой номер",
    "invalid_phone": "некорректный номер",
    "empty_variable": "пустая переменная",
    "duplicate": "дубликат номера",
}


class ImportScreen(ctk.CTkFrame):
    """Экран выбора `.xlsx`, превью контактов и ошибок валидации."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        excel_path: Path | None,
        contacts: list[Contact],
        validation_errors: list[ValidationError],
        on_loaded: Callable[[Path, list[Contact], list[ValidationError]], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._excel_path = excel_path
        self._contacts = contacts
        self._validation_errors = validation_errors
        self._on_loaded = on_loaded

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_file_row()
        self._build_status_row()
        self._build_preview_area()
        self._refresh()

    def _build_file_row(self) -> None:
        file_row = ctk.CTkFrame(self, fg_color="transparent")
        file_row.grid(row=0, column=0, columnspan=2, sticky="ew")
        file_row.grid_columnconfigure(0, weight=1)

        self._file_label = ctk.CTkLabel(file_row, text="", anchor="w")
        self._file_label.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        open_button = ctk.CTkButton(file_row, text="Открыть Excel", command=self._open_file)
        open_button.grid(row=0, column=1)

    def _build_status_row(self) -> None:
        self._status_label = ctk.CTkLabel(self, text="", anchor="w")
        self._status_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(14, 14))

    def _build_preview_area(self) -> None:
        contacts_panel = ctk.CTkFrame(self)
        contacts_panel.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        contacts_panel.grid_columnconfigure(0, weight=1)
        contacts_panel.grid_rowconfigure(1, weight=1)

        contacts_title = ctk.CTkLabel(
            contacts_panel,
            text="Валидные контакты",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        contacts_title.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        self._contacts_list = ctk.CTkScrollableFrame(contacts_panel)
        self._contacts_list.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self._contacts_list.grid_columnconfigure((0, 1, 2), weight=1)

        errors_panel = ctk.CTkFrame(self)
        errors_panel.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        errors_panel.grid_columnconfigure(0, weight=1)
        errors_panel.grid_rowconfigure(1, weight=1)

        errors_title = ctk.CTkLabel(
            errors_panel,
            text="Ошибки импорта",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        errors_title.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        self._errors_list = ctk.CTkScrollableFrame(errors_panel)
        self._errors_list.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self._errors_list.grid_columnconfigure(0, weight=1)

    def _open_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Выберите Excel-файл",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if not selected:
            return

        path = Path(selected)
        try:
            result = load_excel(path)
        except FileNotFoundError:
            self._set_load_error(path, "файл не найден")
            return
        except InvalidExcelFormatError:
            self._set_load_error(path, "файл не удалось прочитать как .xlsx")
            return

        self._excel_path = path
        self._contacts = result.contacts
        self._validation_errors = result.errors
        self._on_loaded(path, result.contacts, result.errors)
        self._refresh()

    def _set_load_error(self, path: Path, message: str) -> None:
        self._excel_path = path
        self._contacts = []
        self._validation_errors = []
        self._on_loaded(path, [], [])
        self._refresh(status_override=f"{path.name}: {message}")

    def _refresh(self, status_override: str | None = None) -> None:
        if self._excel_path is None:
            self._file_label.configure(text="Файл не выбран")
        else:
            self._file_label.configure(text=str(self._excel_path))

        if status_override is not None:
            status_text = status_override
        elif self._excel_path is None:
            status_text = "Контактов: 0 | Ошибок: 0"
        else:
            status_text = (
                f"Контактов: {len(self._contacts)} | "
                f"Ошибок: {len(self._validation_errors)}"
            )
        self._status_label.configure(text=status_text)

        self._render_contacts()
        self._render_errors()

    def _render_contacts(self) -> None:
        _clear_frame(self._contacts_list)

        if not self._contacts:
            self._add_empty_label(self._contacts_list, "Нет валидных контактов")
            return

        headers = ("Строка", "Телефон", "Переменная")
        for column, text in enumerate(headers):
            label = ctk.CTkLabel(
                self._contacts_list,
                text=text,
                font=ctk.CTkFont(weight="bold"),
                anchor="w",
            )
            label.grid(row=0, column=column, padx=6, pady=(0, 6), sticky="ew")

        preview_rows = self._contacts[:MAX_PREVIEW_ROWS]
        for row_index, contact in enumerate(preview_rows, start=1):
            values = (str(contact.row), contact.phone, contact.variable)
            for column, text in enumerate(values):
                label = ctk.CTkLabel(self._contacts_list, text=text, anchor="w")
                label.grid(row=row_index, column=column, padx=6, pady=3, sticky="ew")

        hidden_count = len(self._contacts) - len(preview_rows)
        if hidden_count > 0:
            more_label = ctk.CTkLabel(
                self._contacts_list,
                text=f"Ещё {hidden_count} контактов",
                anchor="w",
                text_color=("gray35", "gray70"),
            )
            more_label.grid(row=len(preview_rows) + 1, column=0, columnspan=3, pady=(8, 0))

    def _render_errors(self) -> None:
        _clear_frame(self._errors_list)

        if not self._validation_errors:
            self._add_empty_label(self._errors_list, "Ошибок нет")
            return

        for row_index, error in enumerate(self._validation_errors):
            text = format_validation_error(error)
            label = ctk.CTkLabel(
                self._errors_list,
                text=text,
                anchor="w",
                justify="left",
                wraplength=340,
            )
            label.grid(row=row_index, column=0, padx=6, pady=4, sticky="ew")

    def _add_empty_label(self, master: ctk.CTkScrollableFrame, text: str) -> None:
        label = ctk.CTkLabel(master, text=text, text_color=("gray35", "gray70"))
        label.grid(row=0, column=0, padx=6, pady=8, sticky="w")


def format_validation_error(error: ValidationError) -> str:
    """Форматирует ошибку Excel-валидации для отображения в UI."""
    reason = _ERROR_LABELS.get(error.reason, error.reason)
    phone = error.raw_phone or "пусто"
    variable = error.raw_variable or "пусто"
    return f"Строка {error.row}: {reason} | номер: {phone} | переменная: {variable}"


def _clear_frame(frame: ctk.CTkScrollableFrame) -> None:
    for child in frame.winfo_children():
        child.destroy()
