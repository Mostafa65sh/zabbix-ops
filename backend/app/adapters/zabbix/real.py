from typing import List, Optional, Dict, Any
import httpx
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.models.schemas import HostSummary, ProblemItem, OverviewData, ProblemCountSummary, InterfaceModel, EventItem



class RealZabbixAdapter(ZabbixAdapterBase):
    """
    Real Zabbix 7.0.5 API Adapter communicating via JSON-RPC 2.0.
    Used exclusively in production or when connected to a real Zabbix server.
    """

    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url
        self.api_token = api_token
        self._request_id = 1

    async def _call_api(self, method: str, params: Dict[str, Any]) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "auth": self.api_token if self.api_token else None,
            "id": self._request_id
        }
        self._request_id += 1

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(self.api_url, json=payload)
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise RuntimeError(f"Zabbix API Error [{data['error'].get('code')}]: {data['error'].get('message')} - {data['error'].get('data')}")
            return data.get("result")

    async def check_connection(self) -> bool:
        try:
            # apiinfo.version does not require authentication in Zabbix
            version = await self._call_api("apiinfo.version", {})
            return bool(version)
        except Exception:
            return False

    async def get_overview(self) -> OverviewData:
        hosts = await self.get_hosts()
        problems = await self.get_problems(limit=1000)

        total = len(hosts)
        up = sum(1 for h in hosts if h.status == "UP")
        down = sum(1 for h in hosts if h.status == "DOWN")
        maint = sum(1 for h in hosts if h.status == "MAINTENANCE")

        sev_summary = ProblemCountSummary(
            total=len(problems),
            disaster=sum(1 for p in problems if p.severity == 5),
            high=sum(1 for p in problems if p.severity == 4),
            average=sum(1 for p in problems if p.severity == 3),
            warning=sum(1 for p in problems if p.severity == 2),
            information=sum(1 for p in problems if p.severity == 1),
        )

        avail_pct = round(((up + maint) / total) * 100, 2) if total > 0 else 100.0

        return OverviewData(
            hosts_total=total,
            hosts_available=up,
            hosts_down=down,
            hosts_maintenance=maint,
            problems_active=len(problems),
            problems_by_severity=sev_summary,
            availability_pct=avail_pct
        )

    async def get_hosts(self, group: Optional[str] = None, status: Optional[str] = None) -> List[HostSummary]:
        params = {
            "output": ["hostid", "host", "name", "status", "maintenance_status"],
            "selectInterfaces": ["interfaceid", "ip", "dns", "port", "type", "main", "available"],
            "selectGroups": ["name"],
            "monitored_hosts": True
        }
        raw_hosts = await self._call_api("host.get", params)
        result = []
        for h in raw_hosts or []:
            h_status = "UP"
            if h.get("maintenance_status") == "1":
                h_status = "MAINTENANCE"
            else:
                interfaces = h.get("interfaces", [])
                if any(str(i.get("available")) == "2" for i in interfaces):
                    h_status = "DOWN"

            groups = [g["name"] for g in h.get("groups", []) if "name" in g]

            if group and not any(group.lower() in g.lower() for g in groups):
                continue
            if status and h_status.upper() != status.upper():
                continue

            parsed_interfaces = [
                InterfaceModel(
                    interfaceid=str(i.get("interfaceid", "")),
                    ip=i.get("ip", ""),
                    dns=i.get("dns", ""),
                    port=i.get("port", ""),
                    type=int(i.get("type", 1)),
                    main=int(i.get("main", 1)),
                    available=int(i.get("available", 0))
                )
                for i in h.get("interfaces", [])
            ]

            result.append(HostSummary(
                id=str(h["hostid"]),
                name=h.get("name") or h.get("host", ""),
                status=h_status,
                groups=groups,
                interfaces=parsed_interfaces
            ))
        return result

    async def get_problems(self, limit: int = 100, severity: Optional[int] = None) -> List[ProblemItem]:
        params = {
            "output": ["eventid", "severity", "name", "clock", "acknowledged"],
            "selectHosts": ["hostid", "name"],
            "recent": True,
            "sortfield": ["eventid"],
            "sortorder": "DESC",
            "limit": limit
        }
        if severity is not None:
            params["severities"] = [severity]

        raw_problems = await self._call_api("problem.get", params)
        result = []
        for p in raw_problems or []:
            host_id = None
            host_name = None
            if p.get("hosts"):
                host_id = str(p["hosts"][0].get("hostid"))
                host_name = p["hosts"][0].get("name")

            result.append(ProblemItem(
                eventid=str(p["eventid"]),
                severity=int(p.get("severity", 0)),
                name=p.get("name", ""),
                clock=int(p.get("clock", 0)),
                acknowledged=bool(int(p.get("acknowledged", 0))),
                host_id=host_id,
                host_name=host_name
            ))
        return result

    async def get_recent_events(self, limit: int = 20) -> List[EventItem]:
        params = {
            "output": ["eventid", "clock", "value", "severity", "name", "acknowledged"],
            "selectHosts": ["hostid", "name"],
            "sortfield": ["clock"],
            "sortorder": "DESC",
            "limit": limit
        }
        raw_events = await self._call_api("event.get", params)
        result = []
        for e in raw_events or []:
            host_id = None
            host_name = None
            if e.get("hosts"):
                host_id = str(e["hosts"][0].get("hostid"))
                host_name = e["hosts"][0].get("name")

            result.append(EventItem(
                eventid=str(e["eventid"]),
                clock=int(e.get("clock", 0)),
                value=int(e.get("value", 1)),
                severity=int(e.get("severity", 0)),
                name=e.get("name", ""),
                host_id=host_id,
                host_name=host_name,
                acknowledged=bool(int(e.get("acknowledged", 0)))
            ))
        return result

