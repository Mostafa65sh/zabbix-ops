from typing import List, Optional, Dict, Any
import time
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.models.schemas import HostSummary, ProblemItem, OverviewData, ProblemCountSummary, InterfaceModel, EventItem



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

    async def get_recent_events(self, limit: int = 20) -> List[EventItem]:
        base_time = 1759230000
        events = [
            EventItem(
                eventid="80001",
                clock=base_time - 1800,
                value=1,
                severity=5,
                name="Host is unreachable by ICMP and agent",
                host_id="10005",
                host_name="DEV-LEGACY-HOST",
                acknowledged=False
            ),
            EventItem(
                eventid="80002",
                clock=base_time - 3600,
                value=1,
                severity=4,
                name="High bandwidth utilization on WAN interface (>95%)",
                host_id="10003",
                host_name="BORDER-GATEWAY-01",
                acknowledged=True
            ),
            EventItem(
                eventid="80003",
                clock=base_time - 5400,
                value=0,
                severity=3,
                name="High memory usage resolved on SERVER-APP-01",
                host_id="10001",
                host_name="SERVER-APP-01",
                acknowledged=True
            ),
            EventItem(
                eventid="80004",
                clock=base_time - 7200,
                value=1,
                severity=2,
                name="Disk space utilization exceeds 85% on /var/log",
                host_id="10001",
                host_name="SERVER-APP-01",
                acknowledged=False
            ),
            EventItem(
                eventid="80005",
                clock=base_time - 10800,
                value=0,
                severity=2,
                name="NTP synchronization restored on SERVER-DB-PRIMARY",
                host_id="10002",
                host_name="SERVER-DB-PRIMARY",
                acknowledged=True
            )
        ]
        return events[:limit]

    async def get_server_inventory(
        self,
        group: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 500,
        offset: int = 0
    ) -> List[dict]:
        servers = [
            {
                "hostid": "10001",
                "host": "server-app-01.corp.internal",
                "name": "SERVER-APP-01",
                "status": "UP",
                "maintenance_status": "0",
                "os": "Ubuntu 22.04.4 LTS (GNU/Linux 5.15.0-101-generic x86_64)",
                "hardware": "Dell PowerEdge R650, 8 vCPU, 32 GB RAM",
                "groups": ["Linux Servers", "Production Applications"],
                "interfaces": [
                    {"interfaceid": "1", "ip": "192.168.10.11", "dns": "app01.corp.internal", "port": "10050", "type": 1, "main": 1, "available": 1, "error": ""}
                ],
                "tags": [
                    {"tag": "environment", "value": "production"},
                    {"tag": "datacenter", "value": "DC-EAST-01"},
                    {"tag": "rack", "value": "RACK-A4"}
                ],
                "inventory": {
                    "os": "Ubuntu 22.04.4 LTS",
                    "os_full": "Ubuntu 22.04.4 LTS (GNU/Linux 5.15.0-101-generic x86_64)",
                    "hardware": "Dell PowerEdge R650, 8 vCPU, 32 GB RAM",
                    "location": "DC-EAST-01",
                    "site_rack": "RACK-A4",
                    "contact": "noc-team@company.internal"
                },
                "metrics": {
                    "cpu_util": 28.5,
                    "cpu_cores": 8,
                    "cpu_load": 1.85,
                    "memory_util": 64.2,
                    "memory_total": 34359738368,
                    "memory_used": 22058952032,
                    "storage_util": 86.4,
                    "storage_total": 536870912000,
                    "storage_used": 463856467968,
                    "net_rx_rate": "45.2 Mbps",
                    "net_tx_rate": "88.7 Mbps"
                }
            },
            {
                "hostid": "10002",
                "host": "server-db-primary.corp.internal",
                "name": "SERVER-DB-PRIMARY",
                "status": "UP",
                "maintenance_status": "0",
                "os": "Red Hat Enterprise Linux 9.3 (Plow)",
                "hardware": "HPE ProLiant DL380 Gen10, 16 vCPU, 64 GB RAM",
                "groups": ["Database Cluster", "Critical Infrastructure"],
                "interfaces": [
                    {"interfaceid": "2", "ip": "192.168.10.20", "dns": "db-pri.corp.internal", "port": "10050", "type": 1, "main": 1, "available": 1, "error": ""}
                ],
                "tags": [
                    {"tag": "tier", "value": "database"},
                    {"tag": "datacenter", "value": "DC-EAST-01"},
                    {"tag": "rack", "value": "RACK-B2"}
                ],
                "inventory": {
                    "os": "Red Hat Enterprise Linux 9.3",
                    "os_full": "Red Hat Enterprise Linux 9.3 (Kernel 5.14.0-362.8.1.el9_3.x86_64)",
                    "hardware": "HPE ProLiant DL380 Gen10, 16 vCPU, 64 GB RAM",
                    "location": "DC-EAST-01",
                    "site_rack": "RACK-B2"
                },
                "metrics": {
                    "cpu_util": 42.1,
                    "cpu_cores": 16,
                    "cpu_load": 3.12,
                    "memory_util": 78.9,
                    "memory_total": 68719476736,
                    "memory_used": 54219667144,
                    "storage_util": 54.0,
                    "storage_total": 2199023255552,
                    "storage_used": 1187472557998,
                    "net_rx_rate": "120.4 Mbps",
                    "net_tx_rate": "210.8 Mbps"
                }
            },
            {
                "hostid": "10003",
                "host": "border-gateway-01.corp.internal",
                "name": "BORDER-GATEWAY-01",
                "status": "UP",
                "maintenance_status": "0",
                "os": "VyOS 1.4-rolling-2023 / Linux 6.1",
                "hardware": "Supermicro 1U Appliance, 4 vCPU, 8 GB RAM",
                "groups": ["Network Devices"],
                "interfaces": [
                    {"interfaceid": "3", "ip": "10.0.0.1", "dns": "gw01.corp.internal", "port": "161", "type": 2, "main": 1, "available": 1, "error": ""}
                ],
                "tags": [
                    {"tag": "role", "value": "router"},
                    {"tag": "datacenter", "value": "DC-EDGE-01"},
                    {"tag": "rack", "value": "RACK-GW1"}
                ],
                "inventory": {
                    "os": "VyOS 1.4",
                    "hardware": "Supermicro 1U Network Appliance, 4 vCPU, 8 GB RAM",
                    "location": "DC-EDGE-01",
                    "site_rack": "RACK-GW1"
                },
                "metrics": {
                    "cpu_util": 15.4,
                    "cpu_cores": 4,
                    "cpu_load": 0.85,
                    "memory_util": 32.0,
                    "memory_total": 8589934592,
                    "memory_used": 2748779069,
                    "storage_util": 18.5,
                    "storage_total": 68719476736,
                    "storage_used": 12713103196,
                    "net_rx_rate": "950 Mbps",
                    "net_tx_rate": "820 Mbps"
                }
            },
            {
                "hostid": "10004",
                "host": "backup-storage-02.corp.internal",
                "name": "BACKUP-STORAGE-02",
                "status": "MAINTENANCE",
                "maintenance_status": "1",
                "os": "TrueNAS SCALE 23.10 / Debian GNU/Linux 12",
                "hardware": "Supermicro 4U Storage, 12 vCPU, 128 GB ECC",
                "groups": ["Storage Systems"],
                "interfaces": [
                    {"interfaceid": "4", "ip": "192.168.30.5", "dns": "nas02.corp.internal", "port": "10050", "type": 1, "main": 1, "available": 1, "error": ""}
                ],
                "tags": [
                    {"tag": "schedule", "value": "weekly-maintenance"},
                    {"tag": "datacenter", "value": "DC-WEST-02"},
                    {"tag": "rack", "value": "RACK-S1"}
                ],
                "inventory": {
                    "os": "TrueNAS SCALE 23.10",
                    "hardware": "Supermicro 4U Storage, 12 vCPU, 128 GB ECC",
                    "location": "DC-WEST-02",
                    "site_rack": "RACK-S1"
                },
                "metrics": {
                    "cpu_util": 8.2,
                    "cpu_cores": 12,
                    "cpu_load": 0.65,
                    "memory_util": 85.0,
                    "memory_total": 137438953472,
                    "memory_used": 116823110451,
                    "storage_util": 71.2,
                    "storage_total": 52776558133248,
                    "storage_used": 37576909390872,
                    "net_rx_rate": "340 Mbps",
                    "net_tx_rate": "12 Mbps"
                }
            },
            {
                "hostid": "10005",
                "host": "dev-legacy-host.corp.internal",
                "name": "DEV-LEGACY-HOST",
                "status": "DOWN",
                "maintenance_status": "0",
                "os": "CentOS Linux release 7.9.2009 (Core)",
                "hardware": "Generic Virtual Machine, 2 vCPU, 4 GB RAM",
                "groups": ["Development Sandbox"],
                "interfaces": [
                    {"interfaceid": "5", "ip": "192.168.50.99", "dns": "legacy01.corp.internal", "port": "10050", "type": 1, "main": 1, "available": 2, "error": "Connection refused on port 10050"}
                ],
                "tags": [
                    {"tag": "env", "value": "sandbox"},
                    {"tag": "datacenter", "value": "DC-DEV-LAB"},
                    {"tag": "rack", "value": "RACK-D0"}
                ],
                "inventory": {
                    "os": "CentOS Linux 7.9.2009",
                    "hardware": "Generic Virtual Machine, 2 vCPU, 4 GB RAM",
                    "location": "DC-DEV-LAB",
                    "site_rack": "RACK-D0"
                },
                "metrics": {
                    "cpu_util": None,
                    "cpu_cores": 2,
                    "cpu_load": None,
                    "memory_util": None,
                    "memory_total": 4294967296,
                    "memory_used": None,
                    "storage_util": None,
                    "storage_total": 85899345920,
                    "storage_used": None,
                    "net_rx_rate": None,
                    "net_tx_rate": None
                }
            },
            {
                "hostid": "10006",
                "host": "server-win-ad01.corp.internal",
                "name": "SERVER-WIN-AD01",
                "status": "UP",
                "maintenance_status": "0",
                "os": "Windows Server 2022 Datacenter (10.0.20348)",
                "hardware": "HPE ProLiant DL360 Gen10, 8 vCPU, 32 GB RAM",
                "groups": ["Windows Servers", "Active Directory"],
                "interfaces": [
                    {"interfaceid": "6", "ip": "192.168.10.15", "dns": "ad01.corp.internal", "port": "10050", "type": 1, "main": 1, "available": 1, "error": ""}
                ],
                "tags": [
                    {"tag": "environment", "value": "production"},
                    {"tag": "role", "value": "domain-controller"},
                    {"tag": "datacenter", "value": "DC-EAST-01"},
                    {"tag": "rack", "value": "RACK-C1"}
                ],
                "inventory": {
                    "os": "Windows Server 2022",
                    "os_full": "Microsoft Windows Server 2022 Datacenter Build 20348",
                    "hardware": "HPE ProLiant DL360 Gen10, 8 vCPU, 32 GB RAM",
                    "location": "DC-EAST-01",
                    "site_rack": "RACK-C1"
                },
                "metrics": {
                    "cpu_util": 12.3,
                    "cpu_cores": 8,
                    "cpu_load": 0.92,
                    "memory_util": 45.8,
                    "memory_total": 34359738368,
                    "memory_used": 15736759972,
                    "storage_util": 38.2,
                    "storage_total": 268435456000,
                    "storage_used": 102542344192,
                    "net_rx_rate": "15.8 Mbps",
                    "net_tx_rate": "22.4 Mbps"
                }
            },
            {
                "hostid": "10007",
                "host": "k8s-worker-01.corp.internal",
                "name": "SERVER-K8S-WORKER-01",
                "status": "UP",
                "maintenance_status": "0",
                "os": "Rocky Linux 9.2 (Blue Onyx)",
                "hardware": "Dell PowerEdge R750, 32 vCPU, 128 GB RAM",
                "groups": ["Linux Servers", "Kubernetes Cluster"],
                "interfaces": [
                    {"interfaceid": "7", "ip": "192.168.20.101", "dns": "k8s-node01.corp.internal", "port": "10050", "type": 1, "main": 1, "available": 1, "error": ""}
                ],
                "tags": [
                    {"tag": "environment", "value": "production"},
                    {"tag": "cluster", "value": "k8s-prod-east"},
                    {"tag": "datacenter", "value": "DC-EAST-02"},
                    {"tag": "rack", "value": "RACK-K1"}
                ],
                "inventory": {
                    "os": "Rocky Linux 9.2",
                    "hardware": "Dell PowerEdge R750, 32 vCPU, 128 GB RAM",
                    "location": "DC-EAST-02",
                    "site_rack": "RACK-K1"
                },
                "metrics": {
                    "cpu_util": 72.8,
                    "cpu_cores": 32,
                    "cpu_load": 18.4,
                    "memory_util": 81.4,
                    "memory_total": 137438953472,
                    "memory_used": 111875308126,
                    "storage_util": 62.0,
                    "storage_total": 1099511627776,
                    "storage_used": 681697209221,
                    "net_rx_rate": "620 Mbps",
                    "net_tx_rate": "740 Mbps"
                }
            },
            {
                "hostid": "10008",
                "host": "monitor-probe-west.corp.internal",
                "name": "MONITOR-PROBE-WEST",
                "status": "UP",
                "maintenance_status": "0",
                "os": "Alpine Linux 3.19.1",
                "hardware": "Edge Micro Compute, 2 vCPU, 2 GB RAM",
                "groups": ["Monitoring Probes"],
                "interfaces": [
                    {"interfaceid": "8", "ip": "10.20.0.50", "dns": "probe-west.corp.internal", "port": "10050", "type": 1, "main": 1, "available": 1, "error": ""}
                ],
                "tags": [
                    {"tag": "role", "value": "probe"},
                    {"tag": "datacenter", "value": "DC-WEST-01"},
                    {"tag": "rack", "value": "RACK-M1"}
                ],
                "inventory": {
                    "os": "Alpine Linux 3.19",
                    "hardware": "Edge Micro Compute, 2 vCPU, 2 GB RAM",
                    "location": "DC-WEST-01",
                    "site_rack": "RACK-M1"
                },
                "metrics": {
                    "cpu_util": 4.1,
                    "cpu_cores": 2,
                    "cpu_load": 0.12,
                    "memory_util": 18.5,
                    "memory_total": 2147483648,
                    "memory_used": 397284475,
                    "storage_util": 12.0,
                    "storage_total": 34359738368,
                    "storage_used": 4123168604,
                    "net_rx_rate": "5.4 Mbps",
                    "net_tx_rate": "8.1 Mbps"
                }
            },
            {
                "hostid": "10009",
                "host": "dev-staging-api.corp.internal",
                "name": "DEV-STAGING-API",
                "status": "UP",
                "maintenance_status": "0",
                "os": "Ubuntu 24.04 LTS (Noble Numbat)",
                "hardware": "KVM Virtual Machine, 4 vCPU, 16 GB RAM",
                "groups": ["Linux Servers", "Development Sandbox"],
                "interfaces": [
                    {"interfaceid": "9", "ip": "192.168.50.25", "dns": "staging-api.corp.internal", "port": "10050", "type": 1, "main": 1, "available": 1, "error": ""}
                ],
                "tags": [
                    {"tag": "env", "value": "staging"},
                    {"tag": "datacenter", "value": "DC-DEV-LAB"},
                    {"tag": "rack", "value": "RACK-D1"}
                ],
                "inventory": {
                    "os": "Ubuntu 24.04 LTS",
                    "hardware": "KVM Virtual Machine, 4 vCPU, 16 GB RAM",
                    "location": "DC-DEV-LAB",
                    "site_rack": "RACK-D1"
                },
                "metrics": {
                    "cpu_util": 19.0,
                    "cpu_cores": 4,
                    "cpu_load": 0.74,
                    "memory_util": 52.3,
                    "memory_total": 17179869184,
                    "memory_used": 8985071583,
                    "storage_util": 41.5,
                    "storage_total": 128849018880,
                    "storage_used": 53472342835,
                    "net_rx_rate": "24.5 Mbps",
                    "net_tx_rate": "32.1 Mbps"
                }
            },
            {
                "hostid": "10010",
                "host": "switch-core-01.corp.internal",
                "name": "SWITCH-CORE-01",
                "status": "UP",
                "maintenance_status": "0",
                "os": "Cisco IOS-XE 17.09.03a",
                "hardware": "Catalyst 9500-48Y4C",
                "groups": ["Network Devices"],
                "interfaces": [
                    {"interfaceid": "10", "ip": "10.0.0.2", "dns": "core-sw01.corp.internal", "port": "161", "type": 2, "main": 1, "available": 1, "error": ""}
                ],
                "tags": [
                    {"tag": "role", "value": "core-switch"},
                    {"tag": "datacenter", "value": "DC-EAST-01"},
                    {"tag": "rack", "value": "RACK-NET1"}
                ],
                "inventory": {
                    "os": "Cisco IOS-XE 17.09",
                    "hardware": "Catalyst 9500-48Y4C",
                    "location": "DC-EAST-01",
                    "site_rack": "RACK-NET1"
                },
                "metrics": {
                    "cpu_util": 22.0,
                    "cpu_cores": 2,
                    "cpu_load": 0.45,
                    "memory_util": 48.0,
                    "memory_total": 4294967296,
                    "memory_used": 2061584302,
                    "storage_util": 30.0,
                    "storage_total": 17179869184,
                    "storage_used": 5153960755,
                    "net_rx_rate": "1250 Mbps",
                    "net_tx_rate": "1180 Mbps"
                }
            }
        ]

        # Apply basic filters
        res = servers
        if group:
            res = [s for s in res if any(group.lower() in g.lower() for g in s.get("groups", []))]
        if status:
            res = [s for s in res if s.get("status", "").upper() == status.upper()]
        if search:
            s_low = search.lower()
            res = [
                s for s in res
                if s_low in s.get("name", "").lower()
                or s_low in s.get("host", "").lower()
                or any(s_low in i.get("ip", "").lower() for i in s.get("interfaces", []))
                or s_low in s.get("os", "").lower()
            ]

        return res[offset : offset + limit]

    def _get_raw_mock_problems(self) -> List[dict]:
        now = int(time.time())
        return [
            {
                "eventid": "90001",
                "source": "0",
                "object": "0",
                "objectid": "20001",
                "clock": str(now - 300),
                "ns": "0",
                "r_eventid": "0",
                "r_clock": "0",
                "name": "Host is unreachable by ICMP and agent",
                "acknowledged": "0",
                "severity": "5",
                "cause_eventid": "0",
                "opdata": "",
                "suppressed": "0",
                "hosts": [{"hostid": "10005", "host": "dev-legacy-host.corp.internal", "name": "DEV-LEGACY-HOST"}],
                "tags": [
                    {"tag": "service", "value": "core-network"},
                    {"tag": "tier", "value": "infra"}
                ],
                "acknowledges": [],
                "suppression_data": [],
                "alerts": [
                    {
                        "alertid": "1",
                        "mediatypeid": "1",
                        "clock": str(now - 290),
                        "sendto": "noc-alerts@company.internal",
                        "status": "1",
                        "error": ""
                    }
                ]
            },
            {
                "eventid": "90002",
                "source": "0",
                "object": "0",
                "objectid": "20002",
                "clock": str(now - 1800),
                "ns": "0",
                "r_eventid": "0",
                "r_clock": "0",
                "name": "WAN interface utilization exceeds 95%",
                "acknowledged": "1",
                "severity": "4",
                "cause_eventid": "0",
                "opdata": "Current util: 96.8 %",
                "suppressed": "0",
                "hosts": [{"hostid": "10003", "host": "border-gateway-01.corp.internal", "name": "BORDER-GATEWAY-01"}],
                "tags": [
                    {"tag": "component", "value": "network"},
                    {"tag": "datacenter", "value": "DC-EDGE-01"}
                ],
                "acknowledges": [
                    {
                        "acknowledgeid": "101",
                        "userid": "1",
                        "clock": str(now - 1200),
                        "message": "Investigating traffic spike with upstream ISP",
                        "action": "6",
                        "old_severity": "0",
                        "new_severity": "0"
                    }
                ],
                "suppression_data": [],
                "alerts": [
                    {
                        "alertid": "2",
                        "mediatypeid": "1",
                        "clock": str(now - 1790),
                        "sendto": "network-ops@company.internal",
                        "status": "1",
                        "error": ""
                    }
                ]
            },
            {
                "eventid": "90003",
                "source": "0",
                "object": "0",
                "objectid": "20003",
                "clock": str(now - 5400),
                "ns": "0",
                "r_eventid": "0",
                "r_clock": "0",
                "name": "High memory usage on application node",
                "acknowledged": "1",
                "severity": "3",
                "cause_eventid": "0",
                "opdata": "84.2 %",
                "suppressed": "0",
                "hosts": [{"hostid": "10001", "host": "server-app-01.corp.internal", "name": "SERVER-APP-01"}],
                "tags": [
                    {"tag": "app", "value": "api-gateway"}
                ],
                "acknowledges": [
                    {
                        "acknowledgeid": "102",
                        "userid": "2",
                        "clock": str(now - 4800),
                        "message": "Pod autoscaling initiated",
                        "action": "2",
                        "old_severity": "0",
                        "new_severity": "0"
                    }
                ],
                "suppression_data": [],
                "alerts": []
            },
            {
                "eventid": "90004",
                "source": "0",
                "object": "0",
                "objectid": "20004",
                "clock": str(now - 1700),
                "ns": "0",
                "r_eventid": "0",
                "r_clock": "0",
                "name": "Packet loss detected on WAN link",
                "acknowledged": "0",
                "severity": "3",
                "cause_eventid": "90002",
                "opdata": "Loss rate: 12%",
                "suppressed": "0",
                "hosts": [{"hostid": "10003", "host": "border-gateway-01.corp.internal", "name": "BORDER-GATEWAY-01"}],
                "tags": [
                    {"tag": "symptom", "value": "true"}
                ],
                "acknowledges": [],
                "suppression_data": [],
                "alerts": []
            },
            {
                "eventid": "90005",
                "source": "0",
                "object": "0",
                "objectid": "20005",
                "clock": str(now - 14400),
                "ns": "0",
                "r_eventid": "0",
                "r_clock": "0",
                "name": "Disk space utilization exceeds 85% on /var/log",
                "acknowledged": "0",
                "severity": "2",
                "cause_eventid": "0",
                "opdata": "86.4 % free: 73.1 GB",
                "suppressed": "0",
                "hosts": [{"hostid": "10001", "host": "server-app-01.corp.internal", "name": "SERVER-APP-01"}],
                "tags": [
                    {"tag": "filesystem", "value": "/var/log"}
                ],
                "acknowledges": [],
                "suppression_data": [],
                "alerts": []
            },
            {
                "eventid": "90006",
                "source": "0",
                "object": "0",
                "objectid": "20006",
                "clock": str(now - 28800),
                "ns": "0",
                "r_eventid": "0",
                "r_clock": "0",
                "name": "Scheduled backup snapshot in progress",
                "acknowledged": "1",
                "severity": "1",
                "cause_eventid": "0",
                "opdata": "Snapshot job #449",
                "suppressed": "1",
                "hosts": [{"hostid": "10004", "host": "backup-storage-02.corp.internal", "name": "BACKUP-STORAGE-02"}],
                "tags": [
                    {"tag": "maintenance", "value": "backup"}
                ],
                "acknowledges": [
                    {
                        "acknowledgeid": "103",
                        "userid": "1",
                        "clock": str(now - 28000),
                        "message": "Expected maintenance window window active",
                        "action": "4",
                        "old_severity": "0",
                        "new_severity": "0"
                    }
                ],
                "suppression_data": [
                    {
                        "maintenanceid": "1",
                        "suppress_until": str(now + 3600)
                    }
                ],
                "alerts": []
            },
            {
                "eventid": "90007",
                "source": "0",
                "object": "0",
                "objectid": "20007",
                "clock": str(now - 86400),
                "ns": "0",
                "r_eventid": "0",
                "r_clock": "0",
                "name": "SSL certificate expires in less than 30 days",
                "acknowledged": "0",
                "severity": "2",
                "cause_eventid": "0",
                "opdata": "Days remaining: 24",
                "suppressed": "0",
                "hosts": [{"hostid": "10006", "host": "server-win-ad01.corp.internal", "name": "SERVER-WIN-AD01"}],
                "tags": [
                    {"tag": "security", "value": "tls"}
                ],
                "acknowledges": [],
                "suppression_data": [],
                "alerts": []
            },
            {
                "eventid": "90008",
                "source": "0",
                "object": "0",
                "objectid": "20008",
                "clock": str(now - 172800),
                "ns": "0",
                "r_eventid": "0",
                "r_clock": "0",
                "name": "Unidentified hardware sensor alert",
                "acknowledged": "0",
                "severity": "0",
                "cause_eventid": "0",
                "opdata": "",
                "suppressed": "0",
                "hosts": [{"hostid": "10002", "host": "server-db-primary.corp.internal", "name": "SERVER-DB-PRIMARY"}],
                "tags": [
                    {"tag": "hardware", "value": "ipmi"}
                ],
                "acknowledges": [],
                "suppression_data": [],
                "alerts": []
            },
            {
                "eventid": "90009",
                "source": "0",
                "object": "0",
                "objectid": "20009",
                "clock": str(now - 1600),
                "ns": "0",
                "r_eventid": "0",
                "r_clock": "0",
                "name": "Database replication latency anomaly",
                "acknowledged": "0",
                "severity": "4",
                "cause_eventid": "90002",
                "opdata": "Delay: 42s",
                "suppressed": "0",
                "hosts": [{"hostid": "10002", "host": "server-db-primary.corp.internal", "name": "SERVER-DB-PRIMARY"}],
                "tags": [
                    {"tag": "db", "value": "replica"}
                ],
                "acknowledges": [],
                "suppression_data": [],
                "alerts": []
            }
        ]

    def _filter_mock_problems(
        self,
        time_from: Optional[int] = None,
        time_till: Optional[int] = None,
        severities: Optional[List[int]] = None,
        acknowledged: Optional[bool] = None,
        suppressed: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[dict]:
        items = self._get_raw_mock_problems()
        res = []
        for p in items:
            clock = int(p.get("clock", 0))
            if time_from is not None and clock < time_from:
                continue
            if time_till is not None and clock > time_till:
                continue
            if severities is not None and int(p.get("severity", 0)) not in severities:
                continue
            if acknowledged is not None:
                p_ack = p.get("acknowledged") == "1"
                if p_ack != acknowledged:
                    continue
            if suppressed is not None:
                p_supp = p.get("suppressed") == "1"
                if p_supp != suppressed:
                    continue
            if search:
                s_lower = search.lower()
                name_match = s_lower in p.get("name", "").lower()
                opdata_match = s_lower in p.get("opdata", "").lower()
                host_match = any(
                    s_lower in h.get("name", "").lower() or s_lower in h.get("host", "").lower()
                    for h in p.get("hosts", [])
                )
                if not (name_match or opdata_match or host_match):
                    continue
            res.append(p)
        return res

    async def get_problem_count(
        self,
        time_from: Optional[int] = None,
        time_till: Optional[int] = None,
        severities: Optional[List[int]] = None,
        acknowledged: Optional[bool] = None,
        suppressed: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        filtered = self._filter_mock_problems(
            time_from=time_from,
            time_till=time_till,
            severities=severities,
            acknowledged=acknowledged,
            suppressed=suppressed,
            search=search
        )
        return len(filtered)

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
        filtered = self._filter_mock_problems(
            time_from=time_from,
            time_till=time_till,
            severities=severities,
            acknowledged=acknowledged,
            suppressed=suppressed,
            search=search
        )

        reverse = (sort_order.upper() == "DESC")
        if sort_field == "severity":
            filtered.sort(key=lambda x: int(x.get("severity", 0)), reverse=reverse)
        elif sort_field == "name":
            filtered.sort(key=lambda x: x.get("name", "").lower(), reverse=reverse)
        elif sort_field == "eventid":
            filtered.sort(key=lambda x: int(x.get("eventid", 0)), reverse=reverse)
        else:
            filtered.sort(key=lambda x: int(x.get("clock", 0)), reverse=reverse)

        return filtered[offset : offset + limit]

    async def get_problem_detail(self, event_id: str) -> Optional[Dict[str, Any]]:
        for p in self._get_raw_mock_problems():
            if str(p.get("eventid")) == str(event_id):
                return p
        return None



