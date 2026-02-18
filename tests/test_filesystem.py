import sys

import pytest

from detect_installer import Installer, detect_installer


def test_pipx_detected(fake_env):
    fake_env(
        {
            "prefix": "home/.local/pipx/venvs/mypkg",
            "installer_value": "pip",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.PIPX


def test_uv_tool_detected(fake_env):
    fake_env(
        {
            "prefix": "home/.local/share/uv/tools/mypkg",
            "installer_value": "uv",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.UV_TOOL


def test_conda_via_env_var(fake_env, tmp_path):
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


@pytest.mark.parametrize("conda_dir", ["miniconda3", "miniforge3", "mambaforge"])
def test_conda_via_path(fake_env, conda_dir):
    fake_env(
        {
            "prefix": f"home/{conda_dir}/envs/myenv",
            "installer_value": "",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.CONDA


def test_mamba_detected(fake_env, tmp_path):
    fake_env(
        {
            "prefix": "conda_env",
            "installer_value": "pip",
            "env": {
                "CONDA_PREFIX": str(tmp_path / "conda_env"),
                "MAMBA_EXE": "/usr/bin/mamba",
            },
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.MAMBA


@pytest.mark.skipif(sys.platform == "win32", reason="brew paths are Unix-only")
def test_brew_macos_arm(fake_env):
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


@pytest.mark.skipif(sys.platform == "win32", reason="brew paths are Unix-only")
def test_brew_macos_intel(fake_env):
    fake_env(
        {
            "prefix": "usr/local/Cellar/python@3.12/3.12.0/Frameworks/Python.framework/Versions/3.12",
            "executable": "usr/local/Cellar/python@3.12/3.12.0/bin/python3",
            "site_packages": "usr/local/Cellar/python@3.12/3.12.0/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages",
            "installer_value": "pip",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.BREW
