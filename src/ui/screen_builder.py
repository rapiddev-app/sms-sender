"""Экран конструктора SMS-шаблона."""

from collections.abc import Callable

import customtkinter as ctk

from core.message_builder import PLACEHOLDER, build_message, count_sms
from core.models import Contact


class BuilderScreen(ctk.CTkFrame):
    """Экран ввода шаблона, счётчика SMS и предпросмотра."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        contacts: list[Contact],
        template: str,
        on_template_changed: Callable[[str], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._contacts = contacts
        self._on_template_changed = on_template_changed

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_editor(template)
        self._build_preview()
        self._refresh()

    def _build_editor(self, template: str) -> None:
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 12))
        toolbar.grid_columnconfigure(0, weight=1)

        self._counter_label = ctk.CTkLabel(toolbar, text="", anchor="w")
        self._counter_label.grid(row=0, column=0, sticky="ew")

        insert_button = ctk.CTkButton(
            toolbar,
            text=PLACEHOLDER,
            width=150,
            command=self._insert_placeholder,
        )
        insert_button.grid(row=0, column=1, padx=(12, 0))

        self._text_box = ctk.CTkTextbox(self, wrap="word")
        self._text_box.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        self._text_box.insert("1.0", template)
        self._text_box.bind("<KeyRelease>", self._handle_text_changed)

    def _build_preview(self) -> None:
        preview_panel = ctk.CTkFrame(self)
        preview_panel.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(8, 0))
        preview_panel.grid_columnconfigure(0, weight=1)
        preview_panel.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(
            preview_panel,
            text="Предпросмотр",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        self._sample_label = ctk.CTkLabel(preview_panel, text="", anchor="w")
        self._sample_label.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")

        self._preview_text = ctk.CTkTextbox(preview_panel, wrap="word", height=220)
        self._preview_text.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._preview_text.configure(state="disabled")

    def _insert_placeholder(self) -> None:
        self._text_box.insert("insert", PLACEHOLDER)
        self._handle_text_changed()

    def _handle_text_changed(self, event: object | None = None) -> None:
        template = self._get_template()
        self._on_template_changed(template)
        self._refresh()

    def _refresh(self) -> None:
        template = self._get_template()
        sample_contact = self._contacts[0] if self._contacts else None
        sample_variable = sample_contact.variable if sample_contact else ""
        preview = build_message(template, sample_variable)
        stats = count_sms(preview)

        self._counter_label.configure(
            text=(
                f"{stats.length} / {stats.per_segment_limit} символов | "
                f"{stats.segments} SMS | {stats.encoding.upper()}"
            )
        )

        if sample_contact is None:
            self._sample_label.configure(text="Нет контактов для предпросмотра")
        else:
            self._sample_label.configure(
                text=f"Пример: строка {sample_contact.row}, {sample_contact.phone}"
            )

        self._preview_text.configure(state="normal")
        self._preview_text.delete("1.0", "end")
        self._preview_text.insert("1.0", preview)
        self._preview_text.configure(state="disabled")

    def _get_template(self) -> str:
        return self._text_box.get("1.0", "end-1c")


def is_template_ready(template: str) -> bool:
    """Возвращает `True`, если шаблон можно передавать на следующий шаг."""
    return bool(template.strip())
