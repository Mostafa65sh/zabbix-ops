from fastapi import APIRouter, Depends
from app.models.schemas import OverviewData
from app.adapters.zabbix.client import get_zabbix_adapter
from app.adapters.zabbix.base import ZabbixAdapterBase

router = APIRouter()


@router.get("/overview", response_model=OverviewData)
async def get_overview(adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)):
    return await adapter.get_overview()
