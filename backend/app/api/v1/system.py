from typing import List, Dict, Any
from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.modules.manager import module_manager
from app.core.modules.status import ModuleInfo

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/modules", response_model=List[ModuleInfo])
async def list_modules():
    """
    Returns the discovery and registration status of all platform modules.
    """
    return module_manager.get_modules()


@router.get("/info")
async def system_info() -> Dict[str, Any]:
    """
    Returns platform Core metadata, version, and module summary statistics.
    """
    modules = module_manager.get_modules()
    enabled_count = sum(1 for m in modules if m.status.value in ("enabled", "loaded"))
    loaded_count = sum(1 for m in modules if m.status.value == "loaded")
    
    return {
        "platform": "Zabbix Operations UI",
        "core_version": settings.CORE_VERSION,
        "environment": settings.APP_ENV,
        "zabbix_adapter": settings.ZABBIX_ADAPTER_TYPE,
        "modules_total": len(modules),
        "modules_enabled": enabled_count,
        "modules_loaded": loaded_count,
    }
