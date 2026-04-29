"""Build the Windows executable with PyInstaller."""

import subprocess
import sys
from pathlib import Path

APP_NAME = "SMS Auto"
PROJECT_ROOT = Path(__file__).resolve().parent
MAIN_SCRIPT = Path("src") / "main.py"
ICON_PATH = Path("assets") / "icon.ico"
ADB_FILES = [
    Path("bin") / "adb" / "adb.exe",
    Path("bin") / "adb" / "AdbWinApi.dll",
    Path("bin") / "adb" / "AdbWinUsbApi.dll",
]
COMPANION_APK = (
    Path("android") / "sms_companion" / "app" / "build" / "outputs" / "apk" / "debug"
    / "app-debug.apk"
)
COMPANION_APK_BUNDLE_DIR = COMPANION_APK.parent
PYINSTALLER_WORK_DIR = Path("build") / "pyinstaller"


class BuildError(Exception):
    """Build cannot continue because required local artifacts are missing."""


def validate_required_files(project_root: Path = PROJECT_ROOT) -> None:
    """Validate files that must exist before PyInstaller starts."""
    required_files = [MAIN_SCRIPT, ICON_PATH, COMPANION_APK, *ADB_FILES]
    missing_files = [path for path in required_files if not (project_root / path).is_file()]

    if not missing_files:
        return

    details = "\n".join(f"  - {path}" for path in missing_files)
    hints: list[str] = []
    if any(path in missing_files for path in ADB_FILES):
        hints.append("Fetch ADB first: uv run python scripts/fetch_adb.py")
    if COMPANION_APK in missing_files:
        hints.append(
            "Build the Android companion first: "
            "cd android/sms_companion; .\\gradlew.bat assembleDebug"
        )
    hint_text = "\n" + "\n".join(hints) if hints else ""
    raise BuildError(f"Missing required build files:\n{details}{hint_text}")


def _add_data_arg(project_root: Path, source: Path, destination: Path) -> str:
    """Build a PyInstaller add-data value with an absolute source path."""
    return f"{(project_root / source).as_posix()}:{destination.as_posix()}"


def build_pyinstaller_args(project_root: Path = PROJECT_ROOT) -> list[str]:
    """Return PyInstaller CLI arguments for the project bundle."""
    return [
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        APP_NAME,
        "--icon",
        str(project_root / ICON_PATH),
        "--paths",
        str(project_root / "src"),
        "--distpath",
        str(project_root / "dist"),
        "--workpath",
        str(project_root / PYINSTALLER_WORK_DIR),
        "--specpath",
        str(project_root / PYINSTALLER_WORK_DIR),
        "--add-data",
        _add_data_arg(project_root, Path("assets"), Path("assets")),
        "--add-data",
        _add_data_arg(project_root, Path("bin") / "adb", Path("bin") / "adb"),
        "--add-data",
        _add_data_arg(project_root, COMPANION_APK, COMPANION_APK_BUNDLE_DIR),
        str(project_root / MAIN_SCRIPT),
    ]


def run_pyinstaller(args: list[str], project_root: Path = PROJECT_ROOT) -> int:
    """Run PyInstaller in the project root and return its exit code."""
    command = [sys.executable, "-m", "PyInstaller", *args]
    result = subprocess.run(command, cwd=project_root, check=False)
    return result.returncode


def main() -> int:
    try:
        validate_required_files()
    except BuildError as exc:
        print(exc, file=sys.stderr)
        return 1

    (PROJECT_ROOT / PYINSTALLER_WORK_DIR).mkdir(parents=True, exist_ok=True)
    return run_pyinstaller(build_pyinstaller_args())


if __name__ == "__main__":
    raise SystemExit(main())
