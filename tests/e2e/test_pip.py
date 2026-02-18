from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .utils import run_cli


def test_pip(tmp_path: Path, library_pkg, venv_python) -> None:
    venv = tmp_path / "venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv)],
        check=True,
        timeout=60,
    )
    py = venv_python(venv)

    subprocess.run(
        [str(py), "-m", "pip", "install", str(library_pkg)],
        check=True,
        capture_output=True,
        timeout=120,
    )
    data = run_cli(py, tmp_path)
    assert data["installer"] == "pip"
