from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.core.logging import get_module_logger
from app.core.auth import require_permission, User
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.adapters.zabbix.client import get_zabbix_adapter
from modules.servers.backend.schemas import (
    ServerListResponseDTO,
    ServerDetailResponseDTO,
    ServerFilterParams
)
from modules.servers.backend.services import ServersService

logger = get_module_logger("servers")
router = APIRouter()


@router.get("", response_model=ServerListResponseDTO)
@router.get("/", response_model=ServerListResponseDTO)
async def list_servers(
    search: Optional[str] = Query(None, description="Search keyword across name, IP, OS, tags"),
    group: Optional[str] = Query(None, description="Filter by Host Group name"),
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(UP|DOWN|MAINTENANCE)$", description="Filter by Host status"),
    availability: Optional[str] = Query(None, pattern="^(AVAILABLE|UNAVAILABLE|UNKNOWN)$", description="Filter by overall availability"),
    os_type: Optional[str] = Query(None, pattern="^(linux|windows|network|other)$", description="Filter by OS family"),
    datacenter: Optional[str] = Query(None, description="Filter by Datacenter / Site"),
    has_problems: Optional[bool] = Query(None, description="Filter hosts with active problems"),
    severity: Optional[int] = Query(None, ge=1, le=5, description="Filter hosts by minimum problem severity (1=Info to 5=Disaster)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("name", pattern="^(name|status|ip|cpu|memory|storage|problems)$", description="Field to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort direction"),
    user: User = Depends(require_permission("module.servers.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve paginated, filtered, and sorted inventory of monitored enterprise servers.
    Includes hardware pressure indicators (CPU/RAM/Disk), network interfaces, OS details,
    tags, and active problem summaries.
    """
    logger.info(f"User '{user.username}' queried Servers list (page={page}, size={page_size}, search='{search}')")
    filters = ServerFilterParams(
        search=search,
        group=group,
        status=status_filter,
        availability=availability,
        os_type=os_type,
        datacenter=datacenter,
        has_problems=has_problems,
        severity=severity,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    service = ServersService(adapter=adapter)
    return await service.get_servers(filters)


@router.get("/status")
async def get_module_status(user: User = Depends(require_permission("module.servers.view"))):
    """
    Internal module readiness and contract status.
    """
    return {
        "module": "servers",
        "name": "Servers",
        "status": "operational",
        "version": "1.0.0",
        "declared_permission": "module.servers.view"
    }


@router.get("/{server_id}", response_model=ServerDetailResponseDTO)
async def get_server_detail(
    server_id: str,
    user: User = Depends(require_permission("module.servers.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve single server 360 detail, including all network interfaces,
    hardware telemetry breakdown, inventory attributes, and active problems.
    """
    logger.info(f"User '{user.username}' requested details for server '{server_id}'")
    service = ServersService(adapter=adapter)
    detail = await service.get_server_by_id(server_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID '{server_id}' was not found in monitoring inventory."
        )
    return detail

