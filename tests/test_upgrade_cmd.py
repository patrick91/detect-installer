import pytest

from detect_installer._detect import _get_upgrade_cmd
from detect_installer._detect import Installer


@pytest.mark.parametrize(
    "installer, expected",
    [
        (Installer.PIP, "pip install -U mypkg"),
        (Installer.UV_PIP, "uv pip install --upgrade mypkg"),
        (Installer.UV, "uv add mypkg --upgrade-package mypkg"),
        (Installer.UV_TOOL, "uv tool upgrade mypkg"),
        (Installer.PIPX, "pipx upgrade mypkg"),
        (Installer.BREW, "brew upgrade mypkg"),
        (Installer.CONDA, "conda update mypkg"),
        (Installer.MAMBA, "mamba update mypkg"),
        (Installer.UNKNOWN, None),
    ],
)
def test_upgrade_command(installer, expected):
    assert _get_upgrade_cmd(installer, "mypkg") == expected


def test_uv_project_lock_strategy():
    assert (
        _get_upgrade_cmd(Installer.UV, "mypkg", uv_upgrade_strategy="lock")
        == "uv lock --upgrade-package mypkg"
    )
