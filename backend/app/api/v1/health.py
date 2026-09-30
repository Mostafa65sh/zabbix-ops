from fastapi import APIRouter, Depends
from app.models.schemas import HealthResponse
from app.core.config import settings
from app.adapters.zabbix.client import get_zabbix_adapter
from app.adapters.zabbix.base import ZabbixAdapterBase

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def check_health(adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)):
    is_connected = await adapter.check_connection()
    return HealthResponse(
        status="healthy" if is_connected else "degraded",
        environment=settings.APP_ENV,
        version="0.1.0",
        zabbix_adapter=settings.ZABBIX_ADAPTER_TYPE,
        zabbix_connected=is_connected
    )
