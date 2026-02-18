from __future__ import annotations

import shutil
import sys
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def project_root():
    return Path(__file__).resolve().parent.parent


@pytest.fixture()
def library_pkg(project_root):
    return project_root


@pytest.fixture()
def venv_python():
    def _venv_python(venv_path: Path) -> Path:
        if sys.platform == "win32":
            return venv_path / "Scripts" / "python.exe"
        return venv_path / "bin" / "python"

    return _venv_python


@pytest.fixture()
def conda_exe():
    conda = shutil.which("conda")
    if conda is None:
        return ["conda"]
    if sys.platform == "win32" and conda.lower().endswith((".bat", ".cmd")):
        return ["cmd", "/c", conda]
    return [conda]


def make_dist_info(
    site_packages: Path, pkg_name: str, installer_value: str | None
) -> Path:
    """Create a minimal dist-info directory with INSTALLER and METADATA files."""
    dist_info = site_packages / f"{pkg_name}-1.0.0.dist-info"
    dist_info.mkdir(parents=True, exist_ok=True)

    (dist_info / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: {pkg_name}\nVersion: 1.0.0\n"
    )

    if installer_value is not None:
        (dist_info / "INSTALLER").write_text(installer_value)

    return dist_info


def make_fake_distribution(dist_info: Path) -> MagicMock:
    """Create a mock distribution that reads files from a real dist-info directory."""
    dist = MagicMock()

    def read_text(filename: str) -> str | None:
        path = dist_info / filename
        if path.exists():
            return path.read_text()
        return None

    dist.read_text = read_text
    return dist


@pytest.fixture()
def fake_env(tmp_path, monkeypatch):
    """Factory fixture that builds a fake installer environment.

    Returns a callable that takes an env spec dict and sets up:
    - Directory structure under tmp_path
    - Monkeypatches sys.prefix, sys.executable, env vars
    - Monkeypatches importlib.metadata.distribution

    The spec dict supports:
        prefix: str - relative path under tmp_path for sys.prefix
        executable: str - relative path under tmp_path for sys.executable
        site_packages: str - relative path under tmp_path for site-packages
        pkg_name: str - package name (default: "mypkg")
        installer_value: str | None - content of INSTALLER file
        env: dict[str, str] - environment variables to set
        extra_files: dict[str, str] - extra files to create (relative to tmp_path)
        no_package: bool - if True, don't create dist-info at all
    """

    def _factory(spec: dict) -> None:
        prefix = tmp_path / spec["prefix"]
        prefix.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("sys.prefix", str(prefix))

        executable = spec.get("executable", spec["prefix"] + "/bin/python3")
        monkeypatch.setattr("sys.executable", str(tmp_path / executable))

        for key, value in spec.get("env", {}).items():
            monkeypatch.setenv(key, value)

        for rel_path, content in spec.get("extra_files", {}).items():
            file_path = tmp_path / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        pkg_name = spec.get("pkg_name", "mypkg")

        if spec.get("no_package"):

            def _raise(name: str):
                raise PackageNotFoundError(name)

            monkeypatch.setattr("detect_installer._detect.distribution", _raise)
        else:
            site_packages_rel = spec.get(
                "site_packages", spec["prefix"] + "/lib/python3.12/site-packages"
            )
            site_packages = tmp_path / site_packages_rel
            site_packages.mkdir(parents=True, exist_ok=True)

            installer_value = spec.get("installer_value")
            dist_info = make_dist_info(site_packages, pkg_name, installer_value)
            fake_dist = make_fake_distribution(dist_info)

            monkeypatch.setattr(
                "detect_installer._detect.distribution", lambda name: fake_dist
            )

    return _factory
