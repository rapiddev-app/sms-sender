"""Локальное JSON-хранилище именованных SMS-шаблонов."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_APPDATA_DIR_NAME = "SMS Auto"
_TEMPLATES_FILENAME = "templates.json"


class TemplateStoreError(Exception):
    """Ошибка чтения или записи хранилища шаблонов."""


class TemplateValidationError(ValueError):
    """Ошибка пользовательских данных шаблона."""


@dataclass(frozen=True)
class SavedTemplate:
    """Именованный SMS-шаблон."""

    name: str
    text: str


def normalize_template_name(name: str) -> str:
    """Нормализует имя шаблона для хранения и сравнения."""
    return " ".join(name.split())


def default_templates_path() -> Path:
    """Возвращает путь к JSON-файлу шаблонов для текущего пользователя."""
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / _APPDATA_DIR_NAME / _TEMPLATES_FILENAME
    return Path.home() / ".sms_auto" / _TEMPLATES_FILENAME


class TemplateStore:
    """Читает и записывает именованные шаблоны в локальный JSON-файл."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or default_templates_path()

    @property
    def path(self) -> Path:
        """Путь к JSON-файлу хранилища."""
        return self._path

    def load_templates(self) -> list[SavedTemplate]:
        """Загружает шаблоны; отсутствующий или повреждённый файл считается пустым."""
        if not self._path.is_file():
            return []

        try:
            raw_data = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        except OSError as exc:
            raise TemplateStoreError(f"Не удалось прочитать шаблоны: {exc}") from exc

        return _parse_templates(raw_data)

    def save_template(self, name: str, text: str) -> list[SavedTemplate]:
        """Создаёт или перезаписывает шаблон и возвращает актуальный список."""
        normalized_name = _validate_template_name(name)
        templates = self.load_templates()
        saved_template = SavedTemplate(name=normalized_name, text=text)

        for index, template in enumerate(templates):
            if template.name == normalized_name:
                templates[index] = saved_template
                break
        else:
            templates.append(saved_template)

        self._write_templates(templates)
        return templates

    def delete_template(self, name: str) -> list[SavedTemplate]:
        """Удаляет шаблон по имени и возвращает актуальный список."""
        normalized_name = _validate_template_name(name)
        templates = [
            template for template in self.load_templates() if template.name != normalized_name
        ]
        self._write_templates(templates)
        return templates

    def _write_templates(self, templates: list[SavedTemplate]) -> None:
        data = {
            "templates": [
                {"name": template.name, "text": template.text} for template in templates
            ]
        }
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
            temporary_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary_path.replace(self._path)
        except OSError as exc:
            raise TemplateStoreError(f"Не удалось сохранить шаблоны: {exc}") from exc


def _validate_template_name(name: str) -> str:
    normalized_name = normalize_template_name(name)
    if not normalized_name:
        raise TemplateValidationError("Введите название шаблона")
    return normalized_name


def _parse_templates(raw_data: Any) -> list[SavedTemplate]:
    if not isinstance(raw_data, dict):
        return []
    raw_templates = raw_data.get("templates")
    if not isinstance(raw_templates, list):
        return []

    templates: list[SavedTemplate] = []
    seen_names: set[str] = set()
    for raw_template in raw_templates:
        if not isinstance(raw_template, dict):
            continue
        name = raw_template.get("name")
        text = raw_template.get("text")
        if not isinstance(name, str) or not isinstance(text, str):
            continue
        normalized_name = normalize_template_name(name)
        if not normalized_name or normalized_name in seen_names:
            continue
        templates.append(SavedTemplate(name=normalized_name, text=text))
        seen_names.add(normalized_name)

    return templates
