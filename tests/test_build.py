"""Tests for the PyInstaller build helper."""

from pathlib import Path

import pytest

import build


def _touch(project_root: Path, relative_path: Path) -> None:
    path = project_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


def test_validate_required_files_accepts_complete_layout(tmp_path) -> None:
    for relative_path in [
        build.MAIN_SCRIPT,
        build.ICON_PATH,
        build.COMPANION_APK,
        *build.ADB_FILES,
    ]:
        _touch(tmp_path, relative_path)

    build.validate_required_files(tmp_path)


def test_validate_required_files_reports_missing_companion_apk(tmp_path) -> None:
    for relative_path in [
        build.MAIN_SCRIPT,
        build.ICON_PATH,
        *build.ADB_FILES,
    ]:
        _touch(tmp_path, relative_path)

    with pytest.raises(build.BuildError, match="assembleDebug"):
        build.validate_required_files(tmp_path)


def test_build_pyinstaller_args_include_resources_and_entrypoint(tmp_path) -> None:
    args = build.build_pyinstaller_args(tmp_path)

    assert "--onefile" in args
    assert "--windowed" in args
    assert "--icon" in args
    assert str(tmp_path / build.MAIN_SCRIPT) == args[-1]
    assert f"{(tmp_path / 'assets').as_posix()}:assets" in args
    assert f"{(tmp_path / 'bin' / 'adb').as_posix()}:bin/adb" in args
    assert (
        f"{(tmp_path / build.COMPANION_APK).as_posix()}:"
        f"{build.COMPANION_APK_BUNDLE_DIR.as_posix()}"
    ) in args
