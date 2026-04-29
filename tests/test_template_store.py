import json

import pytest

from core.template_store import (
    SavedTemplate,
    TemplateStore,
    TemplateValidationError,
    default_templates_path,
    normalize_template_name,
)


def test_normalize_template_name_collapses_whitespace() -> None:
    assert normalize_template_name("  Акция   апрель  ") == "Акция апрель"


def test_load_templates_returns_empty_list_when_file_is_missing(tmp_path) -> None:
    store = TemplateStore(tmp_path / "templates.json")

    assert store.load_templates() == []


def test_save_template_creates_json_file_and_returns_template(tmp_path) -> None:
    path = tmp_path / "templates.json"
    store = TemplateStore(path)

    templates = store.save_template("Приветствие", "Здравствуйте, {переменная}")

    assert templates == [SavedTemplate("Приветствие", "Здравствуйте, {переменная}")]
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "templates": [{"name": "Приветствие", "text": "Здравствуйте, {переменная}"}]
    }


def test_save_template_overwrites_existing_name(tmp_path) -> None:
    store = TemplateStore(tmp_path / "templates.json")

    store.save_template("Приветствие", "Первый текст")
    templates = store.save_template("Приветствие", "Второй текст")

    assert templates == [SavedTemplate("Приветствие", "Второй текст")]


def test_save_template_rejects_blank_name(tmp_path) -> None:
    store = TemplateStore(tmp_path / "templates.json")

    with pytest.raises(TemplateValidationError, match="Введите название шаблона"):
        store.save_template("  ", "Текст")


def test_delete_template_removes_existing_template(tmp_path) -> None:
    store = TemplateStore(tmp_path / "templates.json")
    store.save_template("Первый", "Текст 1")
    store.save_template("Второй", "Текст 2")

    templates = store.delete_template("Первый")

    assert templates == [SavedTemplate("Второй", "Текст 2")]


def test_load_templates_returns_empty_list_for_broken_json(tmp_path) -> None:
    path = tmp_path / "templates.json"
    path.write_text("{broken json", encoding="utf-8")
    store = TemplateStore(path)

    assert store.load_templates() == []


def test_load_templates_ignores_invalid_entries_and_duplicates(tmp_path) -> None:
    path = tmp_path / "templates.json"
    path.write_text(
        json.dumps(
            {
                "templates": [
                    {"name": "Первый", "text": "Текст 1"},
                    {"name": " ", "text": "Пустое имя"},
                    {"name": "Первый", "text": "Дубль"},
                    {"name": "Второй", "text": 123},
                    {"name": "Третий", "text": "Текст 3"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    store = TemplateStore(path)

    assert store.load_templates() == [
        SavedTemplate("Первый", "Текст 1"),
        SavedTemplate("Третий", "Текст 3"),
    ]


def test_default_templates_path_uses_appdata(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))

    assert default_templates_path() == tmp_path / "SMS Auto" / "templates.json"
