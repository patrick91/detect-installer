from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from .utils import has, run_cli

pytestmark = pytest.mark.skipif(
    sys.platform == "win32" and not has("conda"),
    reason="conda not installed",
)


def test_conda(tmp_path: Path, library_pkg, conda_exe) -> None:
    env_path = tmp_path / "conda_env"
    subprocess.run(
        [
            *conda_exe,
            "create",
            "-p",
            str(env_path),
            "python=3.12",
            "pip",
            "-y",
            "--quiet",
        ],
        check=True,
        capture_output=True,
        timeout=300,
    )
    if sys.platform == "win32":
        conda_python = env_path / "python.exe"
    else:
        conda_python = env_path / "bin" / "python"
    subprocess.run(
        [str(conda_python), "-m", "pip", "install", str(library_pkg)],
        check=True,
        capture_output=True,
        timeout=120,
    )
    env = {**os.environ, "CONDA_PREFIX": str(env_path)}
    data = run_cli(conda_python, tmp_path, env=env)
    assert data["installer"] == "conda"
