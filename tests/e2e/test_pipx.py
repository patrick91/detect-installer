import json
import os
import subprocess
from pathlib import Path

import pytest

from .utils import has

pytestmark = pytest.mark.skipif(
    not has("pipx"),
    reason="pipx not installed",
)


def test_pipx(tmp_path: Path, library_pkg) -> None:
    env = {
        **os.environ,
        "PIPX_HOME": str(tmp_path / "pipx"),
        "PIPX_BIN_DIR": str(tmp_path / "bin"),
    }
    subprocess.run(
        ["pipx", "install", str(library_pkg)],
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
    assert data["installer"] == "pipx"
