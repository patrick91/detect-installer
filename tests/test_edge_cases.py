"""Tests for edge cases: missing packages, empty metadata, provenance, etc."""

import pytest

from detect_installer import Installer, InstallerInfo, detect_installer


def test_package_not_found_returns_none(fake_env):
    fake_env({"prefix": "myproject/.venv", "no_package": True})
    assert detect_installer("nonexistent-pkg") is None


def test_empty_installer_file_falls_to_unknown(fake_env):
    fake_env(
        {
            "prefix": "myproject/.venv",
            "installer_value": "",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.UNKNOWN
    assert result.upgrade_cmd is None


def test_no_installer_file_falls_to_unknown(fake_env):
    fake_env(
        {
            "prefix": "myproject/.venv",
            "installer_value": None,
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.UNKNOWN
    assert result.upgrade_cmd is None


def test_unknown_installer_value_falls_to_unknown(fake_env):
    fake_env(
        {
            "prefix": "myproject/.venv",
            "installer_value": "some-unknown-tool",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.UNKNOWN


def test_installer_info_is_frozen():
    info = InstallerInfo(Installer.PIP, "pip install -U mypkg")
    with pytest.raises(AttributeError):
        info.installer = Installer.BREW  # type: ignore[misc]  # ty: ignore[invalid-assignment]


def test_installer_enum_is_str():
    assert Installer.PIP == "pip"
    assert Installer.UV == "uv-project"
    assert Installer.UV_PIP == "uv-pip"
    assert isinstance(Installer.PIP, str)


def test_installer_value_case_insensitive(fake_env):
    """INSTALLER file with uppercase value should still be detected."""
    fake_env(
        {
            "prefix": "myproject/.venv",
            "installer_value": "PIP",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.PIP


def test_installer_value_whitespace_stripped(fake_env):
    """INSTALLER file with surrounding whitespace should still be detected."""
    fake_env(
        {
            "prefix": "myproject/.venv",
            "installer_value": "  pip  \n",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.PIP
