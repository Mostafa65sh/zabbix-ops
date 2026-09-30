import json
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, APIRouter

from app.core.config import settings
from app.core.logging import get_module_logger
from app.core.modules.manifest import ModuleManifest
from app.core.modules.status import ModuleStatus, ModuleInfo
from app.core.modules.version import is_version_compatible

logger = get_module_logger("module_manager")


class ModuleManager:
    """
    Core Module Manager.
    Responsible for module discovery, manifest validation, dependency resolution,
    Core version compatibility checks, dynamic route registration, and lifecycle state.
    """

    def __init__(self, modules_dir: Optional[Path] = None):
        self.modules_dir: Path = modules_dir or settings.resolved_modules_dir
        self.modules: Dict[str, ModuleInfo] = {}
        self._registered_routes: Dict[str, APIRouter] = {}

    def discover_modules(self) -> Dict[str, ModuleInfo]:
        """
        Scans modules directory for subdirectories containing manifest.json.
        """
        self.modules.clear()
        if not self.modules_dir.exists() or not self.modules_dir.is_dir():
            logger.warning(f"Modules directory does not exist: {self.modules_dir}")
            return self.modules

        # Add modules_dir parent to sys.path so modules can be imported as 'modules.<id>.backend...'
        root_dir = str(self.modules_dir.parent)
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)

        for item in sorted(self.modules_dir.iterdir()):
            if not item.is_dir():
                continue

            manifest_path = item / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                manifest = ModuleManifest(**manifest_data)
                
                # Check Core version compatibility
                if not is_version_compatible(settings.CORE_VERSION, manifest.core_version):
                    self.modules[manifest.id] = ModuleInfo(
                        manifest=manifest,
                        status=ModuleStatus.INCOMPATIBLE,
                        error_message=(
                            f"Core version '{settings.CORE_VERSION}' does not satisfy "
                            f"module requirement '{manifest.core_version}'."
                        ),
                        location=str(item)
                    )
                    continue

                # Check if disabled via config
                is_disabled = False
                if manifest.id in settings.disabled_modules_list:
                    is_disabled = True
                elif settings.ENABLED_MODULES != "*":
                    allowed = [m.strip().lower() for m in settings.ENABLED_MODULES.split(",") if m.strip()]
                    if manifest.id not in allowed:
                        is_disabled = True
                elif not manifest.enabled_by_default:
                    is_disabled = True

                initial_status = ModuleStatus.DISABLED if is_disabled else ModuleStatus.ENABLED

                self.modules[manifest.id] = ModuleInfo(
                    manifest=manifest,
                    status=initial_status,
                    location=str(item)
                )

            except Exception as e:
                logger.error(f"Failed to load manifest in {item}: {e}")
                # Create a fallback manifest info if possible
                try:
                    fallback_id = item.name.lower().replace("-", "_")
                    self.modules[fallback_id] = ModuleInfo(
                        manifest=ModuleManifest(
                            id=fallback_id,
                            name=item.name,
                            version="0.0.0",
                            description="Corrupt manifest"
                        ),
                        status=ModuleStatus.ERROR,
                        error_message=str(e),
                        location=str(item)
                    )
                except Exception:
                    pass

        # Resolve dependencies
        self._validate_all_dependencies()

        return self.modules

    def _validate_all_dependencies(self) -> None:
        """
        Validates that all enabled modules have their dependencies met.
        """
        for mod_id, mod_info in self.modules.items():
            if mod_info.status != ModuleStatus.ENABLED:
                continue

            for dep in mod_info.manifest.dependencies:
                if dep not in self.modules:
                    mod_info.status = ModuleStatus.DEPENDENCY_ERROR
                    mod_info.error_message = f"Missing required dependency: '{dep}'"
                    break
                dep_info = self.modules[dep]
                if dep_info.status in (ModuleStatus.DISABLED, ModuleStatus.INCOMPATIBLE, ModuleStatus.ERROR, ModuleStatus.DEPENDENCY_ERROR):
                    mod_info.status = ModuleStatus.DEPENDENCY_ERROR
                    mod_info.error_message = f"Required dependency '{dep}' is not available (status: {dep_info.status.value})"
                    break

    def register_routes(self, app: FastAPI) -> None:
        """
        Mounts backend routes for all enabled and compatible modules into the FastAPI app.
        """
        for mod_id, mod_info in self.modules.items():
            if mod_info.status != ModuleStatus.ENABLED:
                continue

            backend_entry = mod_info.manifest.backend_entry or f"modules.{mod_id}.backend.routes"
            router: Optional[APIRouter] = None

            try:
                # Handle import path like 'modules.overview.backend.routes.router' or 'modules.overview.backend.routes'
                if ":" in backend_entry:
                    mod_path, attr_name = backend_entry.split(":", 1)
                    imported_mod = importlib.import_module(mod_path)
                    router = getattr(imported_mod, attr_name, None)
                elif hasattr(backend_entry, "endswith") and backend_entry.endswith(".router"):
                    mod_path = backend_entry[:-7]
                    imported_mod = importlib.import_module(mod_path)
                    router = getattr(imported_mod, "router", None)
                else:
                    imported_mod = importlib.import_module(backend_entry)
                    router = getattr(imported_mod, "router", None)

                if router and isinstance(router, APIRouter):
                    prefix = f"/api/v1/{mod_id}"
                    app.include_router(router, prefix=prefix, tags=[mod_info.manifest.name])
                    self._registered_routes[mod_id] = router
                    mod_info.status = ModuleStatus.LOADED
                    logger.info(f"Registered routes for module '{mod_id}' at prefix {prefix}")
                else:
                    # If skeleton or router not yet defined, mark as ENABLED
                    logger.info(f"Module '{mod_id}' has no active router; remains ENABLED.")
            except ImportError as ie:
                logger.warning(f"Could not import router for module '{mod_id}': {ie}. Marked as ENABLED.")
            except Exception as e:
                logger.error(f"Error registering routes for module '{mod_id}': {e}")
                mod_info.status = ModuleStatus.ERROR
                mod_info.error_message = str(e)

    def discover_and_register(self, app: FastAPI) -> None:
        """Convenience method to discover modules and register their routes."""
        self.discover_modules()
        self.register_routes(app)

    def enable_module(self, module_id: str) -> bool:
        if module_id not in self.modules:
            return False
        mod = self.modules[module_id]
        if mod.status == ModuleStatus.INCOMPATIBLE:
            return False
        mod.status = ModuleStatus.ENABLED
        mod.error_message = None
        self._validate_all_dependencies()
        return True

    def disable_module(self, module_id: str) -> bool:
        if module_id not in self.modules:
            return False
        self.modules[module_id].status = ModuleStatus.DISABLED
        self._validate_all_dependencies()
        return True

    def get_modules(self) -> List[ModuleInfo]:
        return list(self.modules.values())

    def get_module(self, module_id: str) -> Optional[ModuleInfo]:
        return self.modules.get(module_id)


# Global singleton instance
module_manager = ModuleManager()
