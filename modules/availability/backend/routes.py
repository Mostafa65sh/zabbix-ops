from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.core.logging import get_module_logger
from app.core.auth import require_permission, User
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.adapters.zabbix.client import get_zabbix_adapter
from modules.availability.backend.schemas import (
    AvailabilityOverviewDTO,
    ServiceAvailabilityListDTO,
    SLAListResponseDTO,
    AvailabilityTrendResponseDTO,
    ModuleStatusDTO
)
from modules.availability.backend.services import AvailabilityService

logger = get_module_logger("availability")
router = APIRouter()


@router.get("", response_model=AvailabilityOverviewDTO)
@router.get("/", response_model=AvailabilityOverviewDTO)
async def get_availability_overview(
    time_range: str = Query("30d", pattern="^(24h|7d|30d|90d|365d)$", description="Operational time preset"),
    time_from: Optional[int] = Query(None, ge=0, description="Unix timestamp start of operational window"),
    time_till: Optional[int] = Query(None, ge=0, description="Unix timestamp end of operational window"),
    sla_id: Optional[str] = Query(None, max_length=100, pattern="^[a-zA-Z0-9_-]{1,32}$", description="Filter by SLA ID"),
    user: User = Depends(require_permission("module.availability.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Availability overview telemetry endpoint.
    Aggregates business service availability, SLA compliance rate, total downtime,
    and planned maintenance status.
    """
    logger.info(f"User '{user.username}' requested Availability overview (window={time_range}, sla={sla_id})")
    service = AvailabilityService(adapter=adapter)
    return await service.get_overview(
        time_range=time_range,
        time_from=time_from,
        time_till=time_till,
        sla_id=sla_id
    )


@router.get("/services", response_model=ServiceAvailabilityListDTO)
async def list_services(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    sla_id: Optional[str] = Query(None, max_length=100, pattern="^[a-zA-Z0-9_-]{1,32}$", description="Filter by linked SLA ID"),
    status: Optional[str] = Query(None, pattern="^(OK|WARNING|AVERAGE|HIGH|DISASTER)$", description="Filter by operational status"),
    search: Optional[str] = Query(None, max_length=100, description="Search keyword across service name"),
    sort_by: str = Query("status", pattern="^(name|status|sli|downtime|error_budget)$", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
    user: User = Depends(require_permission("module.availability.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve paginated inventory of monitored business services with operational status,
    active root-cause problem events, and SLI compliance metrics.
    """
    logger.info(f"User '{user.username}' queried Services availability list (page={page}, size={page_size}, search='{search}')")
    service = AvailabilityService(adapter=adapter)
    return await service.get_services(
        page=page,
        page_size=page_size,
        sla_id=sla_id,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/slas", response_model=SLAListResponseDTO)
async def list_slas(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, max_length=100, description="Search keyword across SLA name"),
    sort_by: str = Query("name", pattern="^(name|slo|period)$", description="Field to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort direction"),
    user: User = Depends(require_permission("module.availability.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve paginated registry of configured SLAs, target SLOs, reporting periods,
    and compliance state.
    """
    logger.info(f"User '{user.username}' queried SLAs list (page={page}, size={page_size})")
    service = AvailabilityService(adapter=adapter)
    return await service.get_slas(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/trend", response_model=AvailabilityTrendResponseDTO)
async def get_availability_trend(
    sla_id: str = Query(..., max_length=100, pattern="^[a-zA-Z0-9_-]{1,32}$", description="SLA ID to query trend for"),
    service_id: Optional[str] = Query(None, max_length=100, pattern="^[a-zA-Z0-9_-]{1,32}$", description="Optional service ID to isolate"),
    periods: int = Query(12, ge=1, le=24, description="Number of historical reporting periods to retrieve"),
    user: User = Depends(require_permission("module.availability.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve historical availability and SLI trend for a specified SLA.
    Single-entity lookup strictly targeted by SLA ID.
    """
    logger.info(f"User '{user.username}' requested availability trend for SLA '{sla_id}' (periods={periods})")
    service = AvailabilityService(adapter=adapter)
    try:
        return await service.get_trend(
            sla_id=sla_id,
            service_id=service_id,
            periods=periods
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )


@router.get("/status", response_model=ModuleStatusDTO)
async def get_module_status(user: User = Depends(require_permission("module.availability.view"))):
    """
    Internal module readiness and contract status.
    """
    return ModuleStatusDTO(
        module="availability",
        name="Availability",
        status="operational",
        version="1.0.0",
        declared_permission="module.availability.view"
    )
