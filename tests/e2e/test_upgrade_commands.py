from __future__ import annotations

from collections.abc import Mapping
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .utils import has, run_cli

needs_pipx = pytest.mark.skipif(not has("pipx"), reason="pipx not installed")
needs_uv = pytest.mark.skipif(not has("uv"), reason="uv not installed")

DIST_NAME = "detect-installer-upgrade-probe"
CONSOLE_SCRIPT = "upgrade-probe"
FIXTURE_WHEELS = Path(__file__).resolve().parents[1] / "fixtures" / "wheels"


def publish_probe_wheel(wheelhouse: Path, version: str) -> None:
    """Copy a tiny local-only wheel so upgrade commands can install it."""

    wheel = f"{DIST_NAME.replace('-', '_')}-{version}-py3-none-any.whl"
    shutil.copy(FIXTURE_WHEELS / wheel, wheelhouse / wheel)


@pytest.fixture()
def wheelhouse(tmp_path: Path) -> Path:
    path = tmp_path / "wheelhouse"
    path.mkdir()
    publish_probe_wheel(path, "1.0.0")
    return path


def with_local_wheelhouse(env: Mapping[str, str], wheelhouse: Path) -> dict[str, str]:
    return {
        **env,
        "PIP_NO_INDEX": "1",
        "PIP_FIND_LINKS": str(wheelhouse),
        "UV_NO_INDEX": "1",
        "UV_FIND_LINKS": str(wheelhouse),
    }


def venv_env(venv: Path, wheelhouse: Path) -> dict[str, str]:
    bin_dir = venv / ("Scripts" if sys.platform == "win32" else "bin")
    return with_local_wheelhouse(
        {
            **os.environ,
            "PATH": os.pathsep.join([str(bin_dir), os.environ["PATH"]]),
            "VIRTUAL_ENV": str(venv),
        },
        wheelhouse,
    )


def isolated_pipx_env(tmp_path: Path) -> dict[str, str]:
    return {
        **os.environ,
        "PIPX_HOME": str(tmp_path / "pipx"),
        "PIPX_BIN_DIR": str(tmp_path / "bin"),
    }


def bin_dir(venv: Path) -> Path:
    return venv / ("Scripts" if sys.platform == "win32" else "bin")


def installed_version(python: Path) -> str:
    result = subprocess.run(
        [
            str(python),
            "-c",
            f"from importlib.metadata import version; print(version({DIST_NAME!r}))",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.stdout.strip()


def uv_project_version(project: Path) -> str:
    result = subprocess.run(
        [
            "uv",
            "run",
            "--directory",
            str(project),
            "python",
            "-c",
            f"from importlib.metadata import version; print(version({DIST_NAME!r}))",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.stdout.strip()


def install_probe_with_pip(python: Path, wheelhouse: Path) -> None:
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--find-links",
            str(wheelhouse),
            f"{DIST_NAME}==1.0.0",
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )


def install_probe_with_uv_pip(python: Path, wheelhouse: Path) -> None:
    subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(python),
            "--no-index",
            "--find-links",
            str(wheelhouse),
            f"{DIST_NAME}==1.0.0",
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )


def install_library_with_pip(python: Path, library_pkg: Path) -> None:
    subprocess.run(
        [str(python), "-m", "pip", "install", str(library_pkg)],
        check=True,
        capture_output=True,
        timeout=120,
    )


def install_library_with_uv_pip(python: Path, library_pkg: Path) -> None:
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), str(library_pkg)],
        check=True,
        capture_output=True,
        timeout=120,
    )


def run_upgrade_command(
    command: str, *, env: dict[str, str], cwd: Path | None = None
) -> None:
    publish_probe_wheel(Path(env["PIP_FIND_LINKS"]), "1.1.0")
    subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_pip_upgrade_command_updates_package(
    tmp_path: Path,
    wheelhouse: Path,
    library_pkg,
    venv_python,
) -> None:
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, timeout=60)
    python = venv_python(venv)
    install_probe_with_pip(python, wheelhouse)
    install_library_with_pip(python, library_pkg)

    data = run_cli(python, tmp_path, args=[DIST_NAME])
    assert data["installer"] == "pip"

    run_upgrade_command(data["upgrade_cmd"], env=venv_env(venv, wheelhouse))
    assert installed_version(python) == "1.1.0"


@needs_uv
def test_uv_pip_upgrade_command_updates_package(
    tmp_path: Path,
    wheelhouse: Path,
    library_pkg,
    venv_python,
) -> None:
    venv = tmp_path / "venv"
    subprocess.run(
        ["uv", "venv", str(venv)],
        check=True,
        capture_output=True,
        timeout=60,
    )
    python = venv_python(venv)
    install_probe_with_uv_pip(python, wheelhouse)
    install_library_with_uv_pip(python, library_pkg)

    data = run_cli(python, tmp_path, args=[DIST_NAME])
    assert data["installer"] == "uv-pip"

    run_upgrade_command(data["upgrade_cmd"], env=venv_env(venv, wheelhouse))
    assert installed_version(python) == "1.1.0"


@needs_uv
def test_uv_project_upgrade_command_updates_package(
    tmp_path: Path,
    wheelhouse: Path,
    library_pkg,
) -> None:
    project = tmp_path / "project"
    local_index_env = with_local_wheelhouse(os.environ, wheelhouse)
    subprocess.run(
        ["uv", "init", str(project), "--no-readme"],
        check=True,
        capture_output=True,
        timeout=60,
    )
    subprocess.run(
        [
            "uv",
            "add",
            "--directory",
            str(project),
            "--no-index",
            "--find-links",
            str(wheelhouse),
            DIST_NAME,
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )
    subprocess.run(
        ["uv", "add", "--directory", str(project), str(library_pkg)],
        env=local_index_env,
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
            DIST_NAME,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    data = json.loads(result.stdout)
    assert data["installer"] == "uv-project"

    run_upgrade_command(data["upgrade_cmd"], cwd=project, env=local_index_env)
    assert uv_project_version(project) == "1.1.0"


@needs_uv
def test_uv_tool_upgrade_command_updates_package(
    tmp_path: Path,
    wheelhouse: Path,
    library_pkg,
) -> None:
    env = with_local_wheelhouse(
        {
            **os.environ,
            "UV_TOOL_DIR": str(tmp_path / "uv" / "tools"),
            "UV_TOOL_BIN_DIR": str(tmp_path / "bin"),
        },
        wheelhouse,
    )
    subprocess.run(
        ["uv", "tool", "install", "--with", str(library_pkg), DIST_NAME],
        env=env,
        check=True,
        capture_output=True,
        timeout=120,
    )

    tool_venv = tmp_path / "uv" / "tools" / DIST_NAME
    result = subprocess.run(
        [
            str(
                bin_dir(tool_venv)
                / ("python.exe" if sys.platform == "win32" else "python")
            ),
            "-m",
            "detect_installer._test",
            DIST_NAME,
        ],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    data = json.loads(result.stdout)
    assert data["installer"] == "uv-tool"

    run_upgrade_command(data["upgrade_cmd"], env=env)
    tool = (
        tmp_path
        / "bin"
        / (f"{CONSOLE_SCRIPT}.exe" if sys.platform == "win32" else CONSOLE_SCRIPT)
    )
    result = subprocess.run(
        [str(tool)],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.stdout.strip() == "1.1.0"


@needs_pipx
def test_pipx_upgrade_command_updates_package(
    tmp_path: Path,
    wheelhouse: Path,
    library_pkg,
) -> None:
    env = isolated_pipx_env(tmp_path)
    local_index_env = with_local_wheelhouse(env, wheelhouse)
    subprocess.run(
        ["pipx", "install", DIST_NAME],
        env=local_index_env,
        check=True,
        capture_output=True,
        timeout=120,
    )

    pipx_venv = tmp_path / "pipx" / "venvs" / DIST_NAME
    pipx_python = bin_dir(pipx_venv) / (
        "python.exe" if sys.platform == "win32" else "python"
    )
    install_library_with_uv_pip(pipx_python, library_pkg)

    result = subprocess.run(
        [str(pipx_python), "-m", "detect_installer._test", DIST_NAME],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    data = json.loads(result.stdout)
    assert data["installer"] == "pipx"

    run_upgrade_command(data["upgrade_cmd"], env=local_index_env)
    tool = (
        tmp_path
        / "bin"
        / (f"{CONSOLE_SCRIPT}.exe" if sys.platform == "win32" else CONSOLE_SCRIPT)
    )
    result = subprocess.run(
        [str(tool)],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.stdout.strip() == "1.1.0"
