import sys

import pytest

from detect_installer import Installer, detect_installer


def test_pipx_wins_over_pip_metadata(fake_env):
    """pipx venv with INSTALLER saying 'pip' — pipx should win."""
    fake_env(
        {
            "prefix": "home/.local/pipx/venvs/mypkg",
            "installer_value": "pip",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.PIPX


@pytest.mark.skipif(sys.platform == "win32", reason="brew paths are Unix-only")
def test_brew_wins_over_pip_metadata(fake_env):
    """Homebrew Python with INSTALLER saying 'pip' — brew should win."""
    fake_env(
        {
            "prefix": "opt/homebrew/Frameworks/Python.framework/Versions/3.12",
            "executable": "opt/homebrew/Frameworks/Python.framework/Versions/3.12/bin/python3",
            "site_packages": "opt/homebrew/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages",
            "installer_value": "pip",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.BREW


def test_conda_wins_over_pip_metadata(fake_env, tmp_path):
    """Conda env with INSTALLER saying 'pip' — conda should win."""
    fake_env(
        {
            "prefix": "conda_env",
            "installer_value": "pip",
            "env": {"CONDA_PREFIX": str(tmp_path / "conda_env")},
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.CONDA


def test_uv_tool_wins_over_uv_metadata(fake_env):
    """uv tool path with INSTALLER saying 'uv' — UV_TOOL should win, not UV or UV_PIP."""
    fake_env(
        {
            "prefix": "home/.local/share/uv/tools/mypkg",
            "installer_value": "uv",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.UV_TOOL
