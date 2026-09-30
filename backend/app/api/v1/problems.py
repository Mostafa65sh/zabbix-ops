from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from app.models.schemas import ProblemItem
from app.adapters.zabbix.client import get_zabbix_adapter
from app.adapters.zabbix.base import ZabbixAdapterBase

router = APIRouter()


@router.get("/problems", response_model=List[ProblemItem])
async def list_problems(
    limit: int = Query(100, ge=1, le=1000, description="Max problems to return"),
    severity: Optional[int] = Query(None, ge=0, le=5, description="Filter by problem severity 0-5"),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    return await adapter.get_problems(limit=limit, severity=severity)
