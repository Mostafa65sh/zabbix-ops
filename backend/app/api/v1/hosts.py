from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from app.models.schemas import HostSummary
from app.adapters.zabbix.client import get_zabbix_adapter
from app.adapters.zabbix.base import ZabbixAdapterBase

router = APIRouter()


@router.get("/hosts", response_model=List[HostSummary])
async def list_hosts(
    group: Optional[str] = Query(None, description="Filter hosts by group name"),
    status: Optional[str] = Query(None, description="Filter hosts by status (UP, DOWN, MAINTENANCE)"),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    return await adapter.get_hosts(group=group, status=status)
