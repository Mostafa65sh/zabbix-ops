from app.core.config import settings
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.adapters.zabbix.mock import MockZabbixAdapter
from app.adapters.zabbix.real import RealZabbixAdapter


_adapter_instance = None


def get_zabbix_adapter() -> ZabbixAdapterBase:
    global _adapter_instance
    if _adapter_instance is None:
        if settings.ZABBIX_ADAPTER_TYPE.lower() == "real":
            _adapter_instance = RealZabbixAdapter(
                api_url=settings.ZABBIX_URL,
                api_token=settings.ZABBIX_API_TOKEN
            )
        else:
            _adapter_instance = MockZabbixAdapter()
    return _adapter_instance
