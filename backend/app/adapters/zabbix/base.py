from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.models.schemas import HostSummary, ProblemItem, OverviewData, EventItem


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

    @abstractmethod
    async def get_recent_events(self, limit: int = 20) -> List[EventItem]:
        """Retrieve recent operational events / incidents."""
        pass

    @abstractmethod
    async def get_server_inventory(
        self,
        group: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 500,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve rich server inventory records including hardware metrics, interfaces, and problems."""
        pass

    @abstractmethod
    async def get_problem_count(
        self,
        time_from: Optional[int] = None,
        time_till: Optional[int] = None,
        severities: Optional[List[int]] = None,
        acknowledged: Optional[bool] = None,
        suppressed: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """Count matching active problems using native countOutput: True."""
        pass

    @abstractmethod
    async def get_problem_feed(
        self,
        time_from: Optional[int] = None,
        time_till: Optional[int] = None,
        severities: Optional[List[int]] = None,
        acknowledged: Optional[bool] = None,
        suppressed: Optional[bool] = None,
        search: Optional[str] = None,
        sort_field: str = "clock",
        sort_order: str = "DESC",
        limit: int = 250,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve rich Zabbix 7.0.5 problem records with hosts, tags, opdata, and acknowledges."""
        pass

    @abstractmethod
    async def get_problem_detail(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single problem detail and associated alert history via event.get."""
        pass

    @abstractmethod
    async def get_slas(
        self,
        sla_ids: Optional[List[str]] = None,
        service_ids: Optional[List[str]] = None,
        search: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve SLA definitions with schedule and excluded downtimes via sla.get."""
        pass

    @abstractmethod
    async def get_sla_sli(
        self,
        slaid: str,
        period_from: Optional[int] = None,
        period_to: Optional[int] = None,
        periods: Optional[int] = None,
        service_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Retrieve authoritative SLI calculations for an SLA via sla.getsli."""
        pass

    @abstractmethod
    async def get_services(
        self,
        service_ids: Optional[List[str]] = None,
        sla_ids: Optional[List[str]] = None,
        search: Optional[str] = None,
        status: Optional[int] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Retrieve business services with status, tags, and problem events via service.get."""
        pass




