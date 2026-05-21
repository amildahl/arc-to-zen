#!/usr/bin/env python3
"""Build a one-file desktop executable and package it for release."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "arc-to-zen"


def platform_label() -> str:
    system = platform.system().lower() or "unknown"
    machine = platform.machine().lower() or "unknown"
    aliases = {
        "amd64": "x64",
        "x86_64": "x64",
        "aarch64": "arm64",
    }
    return f"{system}-{aliases.get(machine, machine)}"


def executable_name() -> str:
    return f"{APP_NAME}.exe" if platform.system().lower() == "windows" else APP_NAME


def run_pyinstaller(label: str) -> Path:
    dist_dir = REPO_ROOT / "build" / "dist" / label
    work_dir = REPO_ROOT / "build" / "pyinstaller" / label
    spec_dir = REPO_ROOT / "build" / "pyinstaller" / "spec"

    for path in (dist_dir, work_dir):
        if path.exists():
            shutil.rmtree(path)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--name",
        APP_NAME,
        "--hidden-import",
        "lz4.block",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(spec_dir),
        str(REPO_ROOT / "desktop_app.py"),
    ]
    if platform.system().lower() == "windows":
        command.insert(command.index("--name"), "--windowed")

    subprocess.run(command, cwd=REPO_ROOT, check=True)

    executable = dist_dir / executable_name()
    if not executable.exists():
        raise FileNotFoundError(f"PyInstaller did not create {executable}")

    if platform.system().lower() != "windows":
        executable.chmod(executable.stat().st_mode | 0o755)

    return executable


def package_artifact(executable: Path, label: str, version: str, artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"{APP_NAME}-{version}-{label}"

    if platform.system().lower() == "windows":
        archive = artifact_dir / f"{base_name}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(executable, executable.name)
    else:
        archive = artifact_dir / f"{base_name}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar_file:
            tar_info = tar_file.gettarinfo(executable, executable.name)
            tar_info.mode |= 0o755
            with executable.open("rb") as file_obj:
                tar_file.addfile(tar_info, file_obj)

    return archive


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and package the Arc to Zen desktop app.")
    parser.add_argument("--version", default=os.environ.get("ARC_TO_ZEN_VERSION", "dev"))
    parser.add_argument("--platform-label", default=platform_label())
    parser.add_argument("--artifact-dir", type=Path, default=REPO_ROOT / "release-artifacts")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifact_dir = args.artifact_dir.expanduser()
    if not artifact_dir.is_absolute():
        artifact_dir = REPO_ROOT / artifact_dir

    executable = run_pyinstaller(args.platform_label)
    archive = package_artifact(executable, args.platform_label, args.version, artifact_dir)
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
