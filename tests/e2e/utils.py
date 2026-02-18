import json
import shutil
import subprocess
from pathlib import Path


def run_cli(
    python: Path,
    cwd: Path,
    *,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    """Run the detect-installer _test module and return parsed JSON."""
    cmd = [str(python), "-m", "detect_installer._test", *(args or [])]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        timeout=120,
    )

    assert result.returncode == 0, f"stderr: {result.stderr}"

    return json.loads(result.stdout)


def has(cmd: str) -> bool:
    return shutil.which(cmd) is not None
