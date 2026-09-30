from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.core.logging import get_module_logger
from app.core.auth import require_permission, User
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.adapters.zabbix.client import get_zabbix_adapter
from modules.overview.backend.schemas import OverviewResponseDTO, OverviewFilterParams
from modules.overview.backend.services import OverviewService

logger = get_module_logger("overview")
router = APIRouter()


@router.get("", response_model=OverviewResponseDTO)
@router.get("/", response_model=OverviewResponseDTO)
async def get_overview(
    time_range: str = Query("24h", pattern="^(5m|15m|1h|6h|24h|7d|30d)$", description="Operational time window"),
    group: Optional[str] = Query(None, description="Filter by Host Group"),
    severity: Optional[int] = Query(None, ge=1, le=5, description="Filter by Severity (1=Info to 5=Disaster)"),
    status: Optional[str] = Query(None, pattern="^(UP|DOWN|MAINTENANCE)$", description="Filter by Host status"),

    host: Optional[str] = Query(None, description="Search/Filter by host name"),
    user: User = Depends(require_permission("module.overview.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Overview operations telemetry endpoint.
    Aggregates infrastructure health, hosts, active problems, measured availability,
    top problem hosts, recent incidents, and infrastructure categories.
    """
    logger.info(f"User '{user.username}' requested Overview telemetry (window={time_range}, group={group})")
    filters = OverviewFilterParams(
        time_range=time_range,
        group=group,
        severity=severity,
        status=status,
        host=host
    )
    service = OverviewService(adapter=adapter)
    return await service.get_overview(filters)


@router.get("/status")
async def get_module_status(user: User = Depends(require_permission("module.overview.view"))):
    """
    Internal module readiness and contract status.
    """
    return {
        "module": "overview",
        "name": "Overview",
        "status": "operational",
        "version": "1.0.0",
        "declared_permission": "module.overview.view"
    }
