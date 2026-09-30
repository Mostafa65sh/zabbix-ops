from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.models.schemas import HostSummary, ProblemItem, OverviewData


class ZabbixAdapterBase(ABC):
    """
    Abstract contract for all Zabbix communication.
    The rest of the backend NEVER calls JSON-RPC directly.
    """

    @abstractmethod
    async def check_connection(self) -> bool:
        """Verify connectivity to Zabbix API."""
        pass

    @abstractmethod
    async def get_overview(self) -> OverviewData:
        """Retrieve aggregated infrastructure overview."""
        pass

    @abstractmethod
    async def get_hosts(self, group: Optional[str] = None, status: Optional[str] = None) -> List[HostSummary]:
        """Retrieve normalized hosts with interface and problem summaries."""
        pass

    @abstractmethod
    async def get_problems(self, limit: int = 100, severity: Optional[int] = None) -> List[ProblemItem]:
        """Retrieve recent active problems."""
        pass
