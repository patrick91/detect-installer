from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from .utils import has, run_cli

pytestmark = pytest.mark.skipif(
    not has("uv"),
    reason="uv not installed",
)


def test_uv_pip(tmp_path: Path, library_pkg, venv_python) -> None:
    venv = tmp_path / "venv"
    subprocess.run(
        ["uv", "venv", str(venv)],
        check=True,
        capture_output=True,
        timeout=60,
    )
    py = venv_python(venv)
    subprocess.run(
        ["uv", "pip", "install", "--python", str(py), str(library_pkg)],
        check=True,
        capture_output=True,
        cwd=str(tmp_path),
        timeout=120,
    )
    data = run_cli(py, tmp_path)
    assert data["installer"] == "uv-pip"


def test_uv_project(tmp_path: Path, library_pkg) -> None:
    project = tmp_path / "myproject"
    subprocess.run(
        ["uv", "init", str(project)],
        check=True,
        capture_output=True,
        timeout=60,
    )
    subprocess.run(
        ["uv", "add", "--directory", str(project), str(library_pkg)],
        check=True,
        capture_output=True,
        timeout=120,
    )
    result = subprocess.run(
        [
            "uv",
            "run",
            "--directory",
            str(project),
            "python",
            "-m",
            "detect_installer._test",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["installer"] == "uv-project"


def test_uv_tool(tmp_path: Path, library_pkg) -> None:
    env = {
        **os.environ,
        "UV_TOOL_DIR": str(tmp_path / "uv" / "tools"),
        "UV_TOOL_BIN_DIR": str(tmp_path / "bin"),
    }
    subprocess.run(
        ["uv", "tool", "install", str(library_pkg)],
        check=True,
        capture_output=True,
        env=env,
        timeout=120,
    )
    result = subprocess.run(
        [str(tmp_path / "bin" / "detect-installer-test")],
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["installer"] == "uv-tool"


def test_uv_workspace(tmp_path: Path, library_pkg) -> None:
    workspace = tmp_path / "workspace"

    subprocess.run(
        ["uv", "init", str(workspace), "--no-readme"],
        check=True,
        capture_output=True,
        timeout=60,
    )

    member = workspace / "packages" / "mypkg"
    subprocess.run(
        ["uv", "init", str(member), "--lib", "--no-readme"],
        check=True,
        capture_output=True,
        timeout=60,
    )

    subprocess.run(
        ["uv", "add", "--directory", str(member), str(library_pkg)],
        check=True,
        capture_output=True,
        timeout=120,
    )

    assert (workspace / "uv.lock").exists(), "uv.lock should be at workspace root"
    assert not (member / "uv.lock").exists(), "uv.lock should NOT be in the member"

    result = subprocess.run(
        [
            "uv",
            "run",
            "--directory",
            str(member),
            "python",
            "-m",
            "detect_installer._test",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["installer"] == "uv-project"
