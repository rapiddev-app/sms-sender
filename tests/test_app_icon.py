import tkinter as tk

import app
from app import SMSAutoApp


class FakeRoot:
    def __init__(self, error: Exception | None = None) -> None:
        self.icon_paths: list[str] = []
        self._error = error

    def iconbitmap(self, icon_path: str) -> None:
        if self._error is not None:
            raise self._error
        self.icon_paths.append(icon_path)


def test_asset_path_uses_dev_assets_directory_by_default(monkeypatch) -> None:
    monkeypatch.delattr("sys._MEIPASS", raising=False)

    icon_path = app._asset_path("icon.ico")

    assert icon_path == app._PROJECT_ROOT / "assets" / "icon.ico"


def test_asset_path_uses_pyinstaller_bundle_when_available(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("sys._MEIPASS", str(tmp_path), raising=False)

    icon_path = app._asset_path("icon.ico")

    assert icon_path == tmp_path / "assets" / "icon.ico"


def test_set_window_icon_applies_existing_icon(monkeypatch, tmp_path) -> None:
    icon_path = tmp_path / "icon.ico"
    icon_path.write_bytes(b"icon")
    root = FakeRoot()
    sms_app = SMSAutoApp.__new__(SMSAutoApp)
    sms_app._root = root
    monkeypatch.setattr(app, "_asset_path", lambda _filename: icon_path)

    sms_app._set_window_icon()

    assert root.icon_paths == [str(icon_path)]


def test_set_window_icon_ignores_missing_icon(monkeypatch, tmp_path) -> None:
    root = FakeRoot()
    sms_app = SMSAutoApp.__new__(SMSAutoApp)
    sms_app._root = root
    monkeypatch.setattr(app, "_asset_path", lambda _filename: tmp_path / "missing.ico")

    sms_app._set_window_icon()

    assert root.icon_paths == []


def test_set_window_icon_ignores_tk_icon_error(monkeypatch, tmp_path) -> None:
    icon_path = tmp_path / "icon.ico"
    icon_path.write_bytes(b"icon")
    root = FakeRoot(error=tk.TclError("bad icon"))
    sms_app = SMSAutoApp.__new__(SMSAutoApp)
    sms_app._root = root
    monkeypatch.setattr(app, "_asset_path", lambda _filename: icon_path)

    sms_app._set_window_icon()

    assert root.icon_paths == []
