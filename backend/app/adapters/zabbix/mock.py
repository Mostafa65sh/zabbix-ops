from typing import List, Optional
import time
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.models.schemas import HostSummary, ProblemItem, OverviewData, ProblemCountSummary, InterfaceModel


class MockZabbixAdapter(ZabbixAdapterBase):
    """
    Mock Zabbix Adapter for local offline development.
    Conforms strictly to the Zabbix API data contracts.
    """

    def __init__(self):
        self._mock_hosts = [
            HostSummary(
                id="10001",
                name="SERVER-APP-01",
                status="UP",
                groups=["Linux Servers", "Production Applications"],
                interfaces=[
                    InterfaceModel(interfaceid="1", ip="192.168.10.11", port="10050", available=1)
                ],
                tags=[{"tag": "environment", "value": "production"}],
                maintenance=None,
                problem_summary=ProblemCountSummary(total=1, warning=1)
            ),
            HostSummary(
                id="10002",
                name="SERVER-DB-PRIMARY",
                status="UP",
                groups=["Database Cluster", "Critical Infrastructure"],
                interfaces=[
                    InterfaceModel(interfaceid="2", ip="192.168.10.20", port="10050", available=1)
                ],
                tags=[{"tag": "tier", "value": "database"}],
                maintenance=None,
                problem_summary=ProblemCountSummary(total=0)
            ),
            HostSummary(
                id="10003",
                name="BORDER-GATEWAY-01",
                status="UP",
                groups=["Network Devices"],
                interfaces=[
                    InterfaceModel(interfaceid="3", ip="10.0.0.1", port="161", type=2, available=1)
                ],
                tags=[{"tag": "role", "value": "router"}],
                maintenance=None,
                problem_summary=ProblemCountSummary(total=1, high=1)
            ),
            HostSummary(
                id="10004",
                name="BACKUP-STORAGE-02",
                status="MAINTENANCE",
                groups=["Storage Systems"],
                interfaces=[
                    InterfaceModel(interfaceid="4", ip="192.168.30.5", port="10050", available=1)
                ],
                tags=[{"tag": "schedule", "value": "weekly-maintenance"}],
                maintenance="Scheduled Storage Maintenance",
                problem_summary=ProblemCountSummary(total=0)
            ),
            HostSummary(
                id="10005",
                name="DEV-LEGACY-HOST",
                status="DOWN",
                groups=["Development Sandbox"],
                interfaces=[
                    InterfaceModel(interfaceid="5", ip="192.168.50.99", port="10050", available=2)
                ],
                tags=[{"tag": "env", "value": "sandbox"}],
                maintenance=None,
                problem_summary=ProblemCountSummary(total=1, disaster=1)
            )
        ]

        self._mock_problems = [
            ProblemItem(
                eventid="90001",
                severity=5,
                name="Host is unreachable by ICMP and agent",
                clock=int(time.time()) - 1800,
                acknowledged=False,
                host_id="10005",
                host_name="DEV-LEGACY-HOST"
            ),
            ProblemItem(
                eventid="90002",
                severity=4,
                name="High bandwidth utilization on WAN interface (>95%)",
                clock=int(time.time()) - 3600,
                acknowledged=True,
                host_id="10003",
                host_name="BORDER-GATEWAY-01"
            ),
            ProblemItem(
                eventid="90003",
                severity=2,
                name="Disk space utilization exceeds 85% on /var/log",
                clock=int(time.time()) - 7200,
                acknowledged=False,
                host_id="10001",
                host_name="SERVER-APP-01"
            )
        ]

    async def check_connection(self) -> bool:
        return True

    async def get_overview(self) -> OverviewData:
        hosts = self._mock_hosts
        total = len(hosts)
        up = sum(1 for h in hosts if h.status == "UP")
        down = sum(1 for h in hosts if h.status == "DOWN")
        maint = sum(1 for h in hosts if h.status == "MAINTENANCE")

        sev_summary = ProblemCountSummary(
            total=len(self._mock_problems),
            disaster=sum(1 for p in self._mock_problems if p.severity == 5),
            high=sum(1 for p in self._mock_problems if p.severity == 4),
            average=sum(1 for p in self._mock_problems if p.severity == 3),
            warning=sum(1 for p in self._mock_problems if p.severity == 2),
            information=sum(1 for p in self._mock_problems if p.severity == 1),
        )

        avail_pct = round(((up + maint) / total) * 100, 2) if total > 0 else 100.0

        return OverviewData(
            hosts_total=total,
            hosts_available=up,
            hosts_down=down,
            hosts_maintenance=maint,
            problems_active=len(self._mock_problems),
            problems_by_severity=sev_summary,
            availability_pct=avail_pct
        )

    async def get_hosts(self, group: Optional[str] = None, status: Optional[str] = None) -> List[HostSummary]:
        res = self._mock_hosts
        if group:
            res = [h for h in res if any(group.lower() in g.lower() for g in h.groups)]
        if status:
            res = [h for h in res if h.status.upper() == status.upper()]
        return res

    async def get_problems(self, limit: int = 100, severity: Optional[int] = None) -> List[ProblemItem]:
        res = self._mock_problems
        if severity is not None:
            res = [p for p in res if p.severity == severity]
        return res[:limit]
