from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.core.logging import get_module_logger
from app.core.auth import require_permission, User
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.adapters.zabbix.client import get_zabbix_adapter
from modules.graph_explorer.backend.schemas import (
    GraphExplorerStatusResponse,
    MultiSeriesGraphResponseDTO,
    GraphTargetsResponseDTO
)
from modules.graph_explorer.backend.services import GraphExplorerService

logger = get_module_logger("graph_explorer")
router = APIRouter()


@router.get("/status", response_model=GraphExplorerStatusResponse)
async def get_status(user: User = Depends(require_permission("module.graph_explorer.view"))):
    """
    Internal module readiness and contract status.
    """
    logger.info(f"User '{user.username}' queried Graph Explorer module status")
    return GraphExplorerStatusResponse(
        module="graph_explorer",
        name="Graph Explorer",
        status="operational",
        version="1.0.0",
        declared_permission="module.graph_explorer.view"
    )


@router.get("/targets", response_model=GraphTargetsResponseDTO)
async def get_targets(
    search: Optional[str] = Query(None, description="Search term for host name or IP"),
    group: Optional[str] = Query(None, description="Filter by Host Group"),
    user: User = Depends(require_permission("module.graph_explorer.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve candidate monitored hosts available for multi-series graphing.
    """
    logger.info(f"User '{user.username}' queried Graph Explorer targets (search='{search}', group='{group}')")
    service = GraphExplorerService(adapter=adapter)
    return await service.get_targets(search=search, group=group)


@router.get("/series", response_model=MultiSeriesGraphResponseDTO)
async def get_series(
    host_ids: str = Query(..., description="Comma-separated host IDs to graph (max 10)"),
    metrics: str = Query("cpu", description="Comma-separated metric names (cpu, memory, storage)"),
    time_range: str = Query("24h", pattern="^(1h|6h|12h|24h|7d|30d)$", description="Graph time window"),
    user: User = Depends(require_permission("module.graph_explorer.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve multi-series time-series telemetry data for interactive visualization and comparison.
    """
    logger.info(f"User '{user.username}' requested Graph Explorer series (hosts='{host_ids}', metrics='{metrics}', range='{time_range}')")

    host_id_list = [h.strip() for h in host_ids.split(",") if h.strip()]
    if not host_id_list:
        raise HTTPException(
            status_code=422,
            detail="At least one valid host_id must be provided."
        )

    metric_list = [m.strip().lower() for m in metrics.split(",") if m.strip()]
    allowed_metrics = {"cpu", "memory", "storage"}
    invalid_metrics = [m for m in metric_list if m not in allowed_metrics]
    if invalid_metrics:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported metric(s): {', '.join(invalid_metrics)}. Allowed: {', '.join(allowed_metrics)}"
        )

    service = GraphExplorerService(adapter=adapter)
    return await service.get_multi_series(
        host_ids=host_id_list,
        metrics=metric_list,
        time_range=time_range
    )
