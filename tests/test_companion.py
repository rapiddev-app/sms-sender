"""Tests for shared Android companion helpers."""

from pathlib import Path

from adb import companion


def test_find_companion_apk_returns_dev_path_by_default(monkeypatch, tmp_path) -> None:
    monkeypatch.delattr("sys._MEIPASS", raising=False)
    monkeypatch.setattr(companion, "_PROJECT_ROOT", tmp_path)

    assert companion.find_companion_apk() == tmp_path / companion.COMPANION_APK_RELATIVE_PATH


def test_find_companion_apk_prefers_pyinstaller_bundle_when_available(
    monkeypatch,
    tmp_path,
) -> None:
    bundle_root = tmp_path / "bundle"
    bundled_apk = bundle_root / companion.COMPANION_APK_RELATIVE_PATH
    bundled_apk.parent.mkdir(parents=True)
    bundled_apk.write_bytes(b"apk")

    monkeypatch.setattr("sys._MEIPASS", str(bundle_root), raising=False)
    monkeypatch.setattr(companion, "_PROJECT_ROOT", Path("C:/dev/project"))

    assert companion.find_companion_apk() == bundled_apk


def test_find_companion_apk_falls_back_to_dev_path_when_bundle_file_missing(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr("sys._MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setattr(companion, "_PROJECT_ROOT", tmp_path / "project")

    assert companion.find_companion_apk() == (
        tmp_path / "project" / companion.COMPANION_APK_RELATIVE_PATH
    )
