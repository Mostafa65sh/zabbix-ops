from typing import Optional, List
from fastapi import APIRouter, Depends, Query

from app.core.logging import get_module_logger
from app.core.auth import require_permission, User
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.adapters.zabbix.client import get_zabbix_adapter
from modules.global_search.backend.schemas import (
    GlobalSearchStatusResponse,
    GlobalSearchResponseDTO
)
from modules.global_search.backend.services import GlobalSearchService

logger = get_module_logger("global_search")
router = APIRouter()


@router.get("/status", response_model=GlobalSearchStatusResponse)
async def get_status(user: User = Depends(require_permission("module.global_search.view"))):
    """
    Internal module readiness and operational contract status.
    """
    logger.info(f"User '{user.username}' queried Global Search status")
    return GlobalSearchStatusResponse(
        module="global_search",
        name="Global Search",
        status="operational",
        version="1.0.0",
        declared_permission="module.global_search.view"
    )


@router.get("/query", response_model=GlobalSearchResponseDTO)
async def search(
    q: str = Query("", description="Search term for cross-category lookup"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories: hosts,problems,services,items"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results per category"),
    user: User = Depends(require_permission("module.global_search.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Execute unified global search across hosts, active problems, business services, and metrics.
    Enforces authorization and bounded pagination.
    """
    logger.info(f"User '{user.username}' performed global search: q='{q}', categories='{categories}', limit={limit}")
    
    cat_list: Optional[List[str]] = None
    if categories:
        cat_list = [c.strip() for c in categories.split(",") if c.strip()]

    service = GlobalSearchService(adapter=adapter)
    return await service.search(query=q, categories=cat_list, limit=limit)
