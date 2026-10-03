from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.core.logging import get_module_logger
from app.core.auth import require_permission, User
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.adapters.zabbix.client import get_zabbix_adapter
from modules.top_n.backend.schemas import (
    TopNStatusResponse,
    TopNResponseDTO,
    TopNOverviewResponseDTO
)
from modules.top_n.backend.services import TopNService

logger = get_module_logger("top_n")
router = APIRouter()


@router.get("/status", response_model=TopNStatusResponse)
async def get_status(user: User = Depends(require_permission("module.top_n.view"))):
    """
    Internal module readiness and contract status.
    """
    logger.info(f"User '{user.username}' queried Top N module status")
    return TopNStatusResponse(
        module="top_n",
        name="Top N",
        status="operational",
        version="1.0.0",
        declared_permission="module.top_n.view"
    )


@router.get("/rankings", response_model=TopNResponseDTO)
async def get_rankings(
    metric: str = Query("cpu", pattern="^(cpu|memory|storage|problems)$", description="Resource dimension to rank"),
    limit: int = Query(10, ge=1, le=100, description="Top N limit"),
    order: str = Query("desc", pattern="^(desc|asc)$", description="Sort direction"),
    group: Optional[str] = Query(None, description="Filter by Host Group"),
    user: User = Depends(require_permission("module.top_n.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve ranked list of top monitored hosts for a specific metric dimension.
    """
    logger.info(f"User '{user.username}' requested Top N rankings (metric={metric}, limit={limit}, order={order}, group={group})")
    service = TopNService(adapter=adapter)
    return await service.get_rankings(
        metric=metric,
        limit=limit,
        order=order,
        group=group
    )


@router.get("/overview", response_model=TopNOverviewResponseDTO)
async def get_overview(
    limit: int = Query(5, ge=1, le=25, description="Number of top items per dimension card"),
    group: Optional[str] = Query(None, description="Filter by Host Group"),
    user: User = Depends(require_permission("module.top_n.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve multi-card overview with top ranking hosts across CPU, memory, storage, and incidents.
    """
    logger.info(f"User '{user.username}' requested Top N overview (limit={limit}, group={group})")
    service = TopNService(adapter=adapter)
    return await service.get_overview(limit=limit, group=group)
