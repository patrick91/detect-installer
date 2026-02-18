from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from .utils import has, run_cli

pytestmark = pytest.mark.skipif(
    sys.platform != "darwin" or not has("brew"),
    reason="brew test only runs on macOS with Homebrew",
)


def test_brew(tmp_path: Path, library_pkg) -> None:
    result = subprocess.run(
        ["brew", "--prefix", "python@3.12"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        pytest.skip("python@3.12 not installed via brew")

    brew_prefix = result.stdout.strip()
    brew_python = Path(brew_prefix) / "bin" / "python3.12"
    if not brew_python.exists():
        pytest.skip(f"brew python not found at {brew_python}")

    subprocess.run(
        [
            str(brew_python),
            "-m",
            "pip",
            "install",
            "--break-system-packages",
            str(library_pkg),
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )
    try:
        data = run_cli(brew_python, tmp_path)
        assert data["installer"] == "brew"
    finally:
        subprocess.run(
            [
                str(brew_python),
                "-m",
                "pip",
                "uninstall",
                "-y",
                "detect-installer",
            ],
            capture_output=True,
            timeout=30,
        )
