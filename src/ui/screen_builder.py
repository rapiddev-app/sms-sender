"""Экран конструктора SMS-шаблона."""

from collections.abc import Callable

import customtkinter as ctk

from core.message_builder import PLACEHOLDER, build_message, count_sms
from core.models import Contact
from core.template_store import (
    SavedTemplate,
    TemplateStoreError,
    TemplateValidationError,
    normalize_template_name,
)

_NO_TEMPLATES_TEXT = "Нет сохранённых шаблонов"


class BuilderScreen(ctk.CTkFrame):
    """Экран ввода шаблона, счётчика SMS и предпросмотра."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        contacts: list[Contact],
        template: str,
        templates: list[SavedTemplate],
        on_template_changed: Callable[[str], None],
        on_save_template: Callable[[str, str], list[SavedTemplate]],
        on_delete_template: Callable[[str], list[SavedTemplate]],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._contacts = contacts
        self._templates = templates
        self._on_template_changed = on_template_changed
        self._on_save_template = on_save_template
        self._on_delete_template = on_delete_template

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_template_controls()
        self._build_editor(template)
        self._build_preview()
        self._refresh()

    def _build_template_controls(self) -> None:
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 12))
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=1)

        self._template_name_entry = ctk.CTkEntry(
            controls,
            placeholder_text="Название шаблона",
        )
        self._template_name_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self._template_combo = ctk.CTkComboBox(
            controls,
            values=self._template_names_or_placeholder(),
            command=self._handle_template_selected,
        )
        self._template_combo.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self._template_combo.set(self._initial_template_combo_value())

        save_button = ctk.CTkButton(
            controls,
            text="Сохранить",
            width=110,
            command=self._save_current_template,
        )
        save_button.grid(row=0, column=2, padx=(0, 8))

        self._load_button = ctk.CTkButton(
            controls,
            text="Загрузить",
            width=110,
            command=self._load_selected_template,
        )
        self._load_button.grid(row=0, column=3, padx=(0, 8))

        self._delete_button = ctk.CTkButton(
            controls,
            text="Удалить",
            width=90,
            command=self._delete_selected_template,
        )
        self._delete_button.grid(row=0, column=4)

        self._template_status_label = ctk.CTkLabel(
            controls,
            text="",
            anchor="w",
            text_color=("gray35", "gray70"),
        )
        self._template_status_label.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(6, 0))
        self._refresh_template_controls()

    def _build_editor(self, template: str) -> None:
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 12))
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

        self._template_error_label = ctk.CTkLabel(
            toolbar,
            text="",
            anchor="w",
            text_color=("#b00020", "#ff8a80"),
        )
        self._template_error_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        self._text_box = ctk.CTkTextbox(self, wrap="word")
        self._text_box.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        self._text_box.insert("1.0", template)
        self._text_box.bind("<KeyRelease>", self._handle_text_changed)

    def _build_preview(self) -> None:
        preview_panel = ctk.CTkFrame(self)
        preview_panel.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=(8, 0))
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

    def _handle_template_selected(self, name: str) -> None:
        if name == _NO_TEMPLATES_TEXT:
            return
        self._set_template_name(name)
        self._set_template_status("")
        self._refresh_template_controls()

    def _save_current_template(self) -> None:
        try:
            self._templates = self._on_save_template(
                self._template_name_entry.get(),
                self._get_template(),
            )
        except (TemplateStoreError, TemplateValidationError) as exc:
            self._set_template_status(str(exc), is_error=True)
            return

        selected_name = normalize_template_name(self._template_name_entry.get())
        self._set_template_name(selected_name)
        self._refresh_template_controls(selected_name=selected_name)
        self._set_template_status("Шаблон сохранён")

    def _load_selected_template(self) -> None:
        template = self._selected_template()
        if template is None:
            self._set_template_status("Выберите шаблон", is_error=True)
            return

        self._text_box.delete("1.0", "end")
        self._text_box.insert("1.0", template.text)
        self._on_template_changed(template.text)
        self._refresh()
        self._set_template_name(template.name)
        self._set_template_status("Шаблон загружен")

    def _delete_selected_template(self) -> None:
        template = self._selected_template()
        if template is None:
            self._set_template_status("Выберите шаблон", is_error=True)
            return

        try:
            self._templates = self._on_delete_template(template.name)
        except (TemplateStoreError, TemplateValidationError) as exc:
            self._set_template_status(str(exc), is_error=True)
            return

        self._set_template_name("")
        self._refresh_template_controls()
        self._set_template_status("Шаблон удалён")

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
        self._template_error_label.configure(text=build_template_error(template))

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

    def _template_names_or_placeholder(self) -> list[str]:
        names = [template.name for template in self._templates]
        return names or [_NO_TEMPLATES_TEXT]

    def _initial_template_combo_value(self) -> str:
        names = self._template_names_or_placeholder()
        return names[0]

    def _selected_template(self) -> SavedTemplate | None:
        selected_name = self._template_combo.get()
        return next(
            (template for template in self._templates if template.name == selected_name),
            None,
        )

    def _refresh_template_controls(self, selected_name: str | None = None) -> None:
        names = self._template_names_or_placeholder()
        has_templates = bool(self._templates)
        self._template_combo.configure(values=names)

        if selected_name and selected_name in names:
            self._template_combo.set(selected_name)
        elif has_templates and self._template_combo.get() not in names:
            self._template_combo.set(names[0])
        elif not has_templates:
            self._template_combo.set(_NO_TEMPLATES_TEXT)

        state = "normal" if has_templates else "disabled"
        self._load_button.configure(state=state)
        self._delete_button.configure(state=state)

    def _set_template_name(self, name: str) -> None:
        self._template_name_entry.delete(0, "end")
        if name:
            self._template_name_entry.insert(0, name)

    def _set_template_status(self, text: str, *, is_error: bool = False) -> None:
        color = ("#b00020", "#ff8a80") if is_error else ("gray35", "gray70")
        self._template_status_label.configure(text=text, text_color=color)


def is_template_ready(template: str) -> bool:
    """Возвращает `True`, если шаблон можно передавать на следующий шаг."""
    return bool(template.strip())


def build_template_error(template: str) -> str:
    """Возвращает сообщение об ошибке шаблона или пустую строку."""
    if is_template_ready(template):
        return ""
    return "Введите текст SMS-шаблона"
