import pytest
import json
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.core.modules.manager import ModuleManager
from app.core.modules.manifest import ModuleManifest
from app.core.modules.status import ModuleStatus
from app.core.modules.version import is_version_compatible, parse_semver
from app.core.logging import get_module_logger
from app.core.auth import User, has_permission, LocalDevAuthProvider


def test_semver_parser_and_compatibility():
    # Parsing
    assert parse_semver("0.2.0") == (0, 2, 0)
    assert parse_semver("v1.5.12") == (1, 5, 12)
    assert parse_semver("2.0") == (2, 0, 0)

    # Range and operators
    assert is_version_compatible("0.2.0", ">=0.2.0") is True
    assert is_version_compatible("0.1.9", ">=0.2.0") is False
    assert is_version_compatible("0.2.5", ">=0.2.0, <1.0.0") is True
    assert is_version_compatible("1.0.0", ">=0.2.0, <1.0.0") is False
    assert is_version_compatible("0.2.0", "*") is True
    assert is_version_compatible("0.2.0", "==0.2.0") is True
    assert is_version_compatible("0.3.0", "==0.2.0") is False
    assert is_version_compatible("0.2.4", "^0.2.0") is True
    assert is_version_compatible("0.3.0", "^0.2.0") is False


def test_manifest_validation():
    # Valid manifest
    manifest_data = {
        "id": "test_mod",
        "name": "Test Module",
        "version": "1.0.0",
        "description": "Test description",
        "core_version": ">=0.2.0",
        "dependencies": ["overview"]
    }
    manifest = ModuleManifest(**manifest_data)
    assert manifest.id == "test_mod"
    assert manifest.name == "Test Module"

    # Invalid ID with uppercase or spaces
    with pytest.raises(ValueError):
        ModuleManifest(id="Invalid ID", name="Invalid", version="1.0.0")


def test_module_discovery_and_enable_disable(tmp_path: Path):
    # Setup temporary modules directory
    mod_a_dir = tmp_path / "module_a"
    mod_a_dir.mkdir()
    (mod_a_dir / "manifest.json").write_text(json.dumps({
        "id": "module_a",
        "name": "Module A",
        "version": "0.1.0",
        "core_version": ">=0.2.0",
        "enabled_by_default": True
    }), encoding="utf-8")

    mod_b_dir = tmp_path / "module_b"
    mod_b_dir.mkdir()
    (mod_b_dir / "manifest.json").write_text(json.dumps({
        "id": "module_b",
        "name": "Module B",
        "version": "0.1.0",
        "core_version": ">=0.2.0",
        "enabled_by_default": True,
        "dependencies": ["module_a"]
    }), encoding="utf-8")

    manager = ModuleManager(modules_dir=tmp_path)
    discovered = manager.discover_modules()

    assert "module_a" in discovered
    assert "module_b" in discovered
    assert discovered["module_a"].status == ModuleStatus.ENABLED
    assert discovered["module_b"].status == ModuleStatus.ENABLED

    # Disable module_a -> module_b should fail dependency check
    manager.disable_module("module_a")
    assert discovered["module_a"].status == ModuleStatus.DISABLED
    assert discovered["module_b"].status == ModuleStatus.DEPENDENCY_ERROR

    # Re-enable module_a -> module_b becomes ENABLED
    manager.enable_module("module_a")
    assert discovered["module_a"].status == ModuleStatus.ENABLED
    # Re-validate
    manager.enable_module("module_b")
    assert discovered["module_b"].status == ModuleStatus.ENABLED


def test_core_version_incompatibility(tmp_path: Path):
    mod_dir = tmp_path / "incompatible_mod"
    mod_dir.mkdir()
    (mod_dir / "manifest.json").write_text(json.dumps({
        "id": "incompatible_mod",
        "name": "Incompatible",
        "version": "1.0.0",
        "core_version": ">=9.0.0",  # Far in the future
        "enabled_by_default": True
    }), encoding="utf-8")

    manager = ModuleManager(modules_dir=tmp_path)
    discovered = manager.discover_modules()

    assert "incompatible_mod" in discovered
    assert discovered["incompatible_mod"].status == ModuleStatus.INCOMPATIBLE
    assert "does not satisfy module requirement" in discovered["incompatible_mod"].error_message


def test_missing_dependency(tmp_path: Path):
    mod_dir = tmp_path / "mod_missing_dep"
    mod_dir.mkdir()
    (mod_dir / "manifest.json").write_text(json.dumps({
        "id": "mod_missing_dep",
        "name": "Missing Dep",
        "version": "1.0.0",
        "core_version": ">=0.2.0",
        "dependencies": ["non_existent_module"]
    }), encoding="utf-8")

    manager = ModuleManager(modules_dir=tmp_path)
    discovered = manager.discover_modules()

    assert "mod_missing_dep" in discovered
    assert discovered["mod_missing_dep"].status == ModuleStatus.DEPENDENCY_ERROR
    assert "Missing required dependency" in discovered["mod_missing_dep"].error_message


def test_logging_module_tag():
    logger = get_module_logger("test_logging")
    assert logger.extra["module_id"] == "test_logging"


def test_core_permissions():
    admin = User(id="1", username="admin", is_superuser=True)
    assert has_permission(admin, "module.overview.view") is True

    operator = User(id="2", username="op", is_superuser=False, permissions=["module.overview.*"])
    assert has_permission(operator, "module.overview.view") is True
    assert has_permission(operator, "module.network.view") is False

    viewer = User(id="3", username="view", is_superuser=False, permissions=["module.overview.view"])
    assert has_permission(viewer, "module.overview.view") is True
    assert has_permission(viewer, "module.overview.edit") is False


@pytest.mark.asyncio
async def test_system_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # System info
        info_resp = await client.get("/api/v1/system/info")
        assert info_resp.status_code == 200
        info_data = info_resp.json()
        assert info_data["core_version"] == "0.2.0"
        assert info_data["platform"] == "Zabbix Operations UI"
        assert info_data["modules_total"] >= 21

        # System modules
        modules_resp = await client.get("/api/v1/system/modules")
        assert modules_resp.status_code == 200
        modules_data = modules_resp.json()
        assert isinstance(modules_data, list)
        assert len(modules_data) >= 21

        # Check that overview module is present
        overview_mod = next((m for m in modules_data if m["manifest"]["id"] == "overview"), None)
        assert overview_mod is not None
        assert overview_mod["status"] in ("enabled", "loaded")


@pytest.mark.asyncio
async def test_module_skeleton_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Module route mounted under /api/v1/servers/status (skeleton)
        resp = await client.get("/api/v1/servers/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "servers"
        assert data["status"] == "skeleton"

        # Overview module status (now operational in Phase 1)
        ov_resp = await client.get("/api/v1/overview/status")
        assert ov_resp.status_code == 200
        ov_data = ov_resp.json()
        assert ov_data["module"] == "overview"
        assert ov_data["status"] == "operational"

