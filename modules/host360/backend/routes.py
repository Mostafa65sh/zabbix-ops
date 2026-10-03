from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.core.logging import get_module_logger
from app.core.auth import require_permission, User
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.adapters.zabbix.client import get_zabbix_adapter
from modules.host360.backend.schemas import (
    Host360StatusResponse,
    Host360ListResponseDTO,
    Host360DetailDTO,
    Host360TelemetryResponseDTO
)
from modules.host360.backend.services import Host360Service

logger = get_module_logger("host360")
router = APIRouter()


@router.get("/status", response_model=Host360StatusResponse)
async def get_status(user: User = Depends(require_permission("module.host360.view"))):
    """
    Internal module readiness and contract status.
    """
    logger.info(f"User '{user.username}' queried Host 360 module status")
    return Host360StatusResponse(
        module="host360",
        name="Host 360",
        status="operational",
        version="1.0.0",
        declared_permission="module.host360.view"
    )


@router.get("/hosts", response_model=Host360ListResponseDTO)
async def list_hosts(
    search: Optional[str] = Query(None, description="Search term for host name, IP, OS, or datacenter"),
    group: Optional[str] = Query(None, description="Filter by Host Group"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    user: User = Depends(require_permission("module.host360.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve list of monitored hosts for selection and quick status overview in Host 360.
    """
    logger.info(f"User '{user.username}' requested Host 360 hosts list (search='{search}', group='{group}')")
    service = Host360Service(adapter=adapter)
    return await service.list_hosts(
        search=search,
        group=group,
        page=page,
        page_size=page_size
    )


@router.get("/{host_id}", response_model=Host360DetailDTO)
async def get_host_360_detail(
    host_id: str,
    user: User = Depends(require_permission("module.host360.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve comprehensive 360-degree telemetry and profile for a specific host.
    Includes hardware metrics, interfaces, tags, inventory, active problems, and data lineage.
    """
    logger.info(f"User '{user.username}' requested 360 detail for host '{host_id}'")
    service = Host360Service(adapter=adapter)
    detail = await service.get_host_360_detail(host_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID '{host_id}' was not found in monitoring inventory."
        )
    return detail


@router.get("/{host_id}/telemetry", response_model=Host360TelemetryResponseDTO)
async def get_host_telemetry(
    host_id: str,
    time_range: str = Query("24h", pattern="^(1h|6h|12h|24h|7d|30d)$", description="Telemetry time window"),
    user: User = Depends(require_permission("module.host360.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve historical time-series metric data (CPU, memory, storage utilization)
    for interactive telemetry charts.
    """
    logger.info(f"User '{user.username}' requested telemetry history for host '{host_id}' (range='{time_range}')")
    service = Host360Service(adapter=adapter)
    telemetry = await service.get_host_telemetry_series(host_id=host_id, time_range=time_range)
    if not telemetry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with ID '{host_id}' was not found in monitoring inventory."
        )
    return telemetry
