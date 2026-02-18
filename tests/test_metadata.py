from detect_installer import Installer, detect_installer


def test_uv_project_with_lock(fake_env):
    fake_env(
        {
            "prefix": "myproject/.venv",
            "installer_value": "uv",
            "extra_files": {"myproject/uv.lock": ""},
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.UV
    assert result.upgrade_cmd is not None
    assert "uv add" in result.upgrade_cmd


def test_uv_standalone_no_lock(fake_env):
    fake_env(
        {
            "prefix": "somedir/.venv",
            "installer_value": "uv",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.UV_PIP
    assert result.upgrade_cmd is not None
    assert "uv pip install" in result.upgrade_cmd


def test_uv_lock_two_levels_up(fake_env):
    """Workspace scenario: uv.lock is at workspace root, venv is nested deeper."""
    fake_env(
        {
            "prefix": "workspace/packages/mypkg/.venv",
            "installer_value": "uv",
            "extra_files": {"workspace/uv.lock": ""},
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.UV


def test_uv_lock_three_levels_up(fake_env):
    """uv.lock exactly 3 levels up from sys.prefix — should still be found."""
    fake_env(
        {
            "prefix": "a/b/c/.venv",
            "installer_value": "uv",
            "extra_files": {"a/uv.lock": ""},
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.UV


def test_uv_lock_four_levels_up_not_found(fake_env):
    """uv.lock 4 levels up — beyond the 3-level walk, should fall back to UV_PIP."""
    fake_env(
        {
            "prefix": "a/b/c/d/.venv",
            "installer_value": "uv",
            "extra_files": {"a/uv.lock": ""},
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.UV_PIP


def test_pip_detected(fake_env):
    fake_env(
        {
            "prefix": "myproject/.venv",
            "installer_value": "pip",
        }
    )
    result = detect_installer("mypkg")
    assert result is not None
    assert result.installer is Installer.PIP
