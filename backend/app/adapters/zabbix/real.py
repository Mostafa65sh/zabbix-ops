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

    async def get_server_inventory(
        self,
        group: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 500,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        # Zabbix host.get does NOT support 'offset' in CApiInputValidator (Zabbix 7.0.5).
        # We retrieve a bounded candidate set (up to limit + offset, capped at 1000)
        # and safely slice client-side without unbounded memory consumption or N+1 queries.
        bounded_limit = min(max(limit + offset, 1), 1000)
        params: Dict[str, Any] = {
            "output": ["hostid", "host", "name", "status", "maintenance_status", "description"],
            "selectInterfaces": ["interfaceid", "ip", "dns", "port", "type", "main", "available", "error"],
            "selectGroups": ["groupid", "name"],
            "selectInventory": ["os", "os_full", "hardware", "software", "contact", "location", "site_rack", "tag", "notes"],
            "selectTags": ["tag", "value"],
            "monitored_hosts": True,
            "limit": bounded_limit
        }
        if search:
            params["search"] = {"name": search, "host": search}
            params["searchByAny"] = True

        raw_hosts = await self._call_api("host.get", params) or []
        if not raw_hosts:
            return []

        # Safe client-side pagination slice preserving application contract
        paged_hosts = raw_hosts[offset : offset + limit] if offset > 0 or len(raw_hosts) > limit else raw_hosts
        if not paged_hosts:
            return []

        hostids = [str(h["hostid"]) for h in paged_hosts]

        # Batch item queries without N+1 requests
        items_by_host: Dict[str, Dict[str, Dict[str, Any]]] = {hid: {} for hid in hostids}
        itemids_float: List[str] = []
        try:
            raw_items = await self._call_api("item.get", {
                "output": ["itemid", "hostid", "key_", "name", "value_type", "units"],
                "hostids": hostids,
                "filter": {
                    "key_": [
                        "system.cpu.util",
                        "system.cpu.num",
                        "system.cpu.load[all,avg1]",
                        "vm.memory.util",
                        "vm.memory.size[total]",
                        "vm.memory.size[used]",
                        "vfs.fs.size[/,pused]",
                        "vfs.fs.size[/,total]",
                        "vfs.fs.size[/,used]",
                        "system.uname",
                        "system.sw.os"
                    ]
                }
            }) or []
            for it in raw_items:
                hid = str(it.get("hostid"))
                key = it.get("key_")
                if hid in items_by_host and key:
                    items_by_host[hid][key] = it
                    # Collect float items for history.get (value_type 0 = float, 3 = uint)
                    val_type = str(it.get("value_type", "0"))
                    if val_type in ("0", "3") and key in ("system.cpu.util", "vm.memory.util", "vfs.fs.size[/,pused]"):
                        itemids_float.append(str(it["itemid"]))
        except Exception:
            pass

        # In Zabbix 7.0.5, lastvalue was removed from items table.
        # Retrieve latest telemetry values via a single batched history.get call.
        history_values: Dict[str, float] = {}
        if itemids_float:
            try:
                raw_history = await self._call_api("history.get", {
                    "output": ["itemid", "clock", "value"],
                    "history": 0,  # 0 = numeric float
                    "itemids": itemids_float,
                    "sortfield": "clock",
                    "sortorder": "DESC",
                    "limit": len(itemids_float) * 5
                }) or []
                for entry in raw_history:
                    iid = str(entry.get("itemid"))
                    # Since sorted by clock DESC, first occurrence is the latest value
                    if iid not in history_values:
                        try:
                            history_values[iid] = float(entry.get("value"))
                        except (ValueError, TypeError):
                            pass
            except Exception:
                pass

        result = []
        for h in paged_hosts:
            hid = str(h["hostid"])
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

            host_items = items_by_host.get(hid, {})
            inv = h.get("inventory") or {}
            if not isinstance(inv, dict):
                inv = {}

            # Resolve telemetry from batch history values without fabrication (Golden Rule)
            cpu_val = None
            if "system.cpu.util" in host_items:
                cpu_itemid = str(host_items["system.cpu.util"].get("itemid", ""))
                cpu_val = history_values.get(cpu_itemid)

            mem_val = None
            if "vm.memory.util" in host_items:
                mem_itemid = str(host_items["vm.memory.util"].get("itemid", ""))
                mem_val = history_values.get(mem_itemid)

            storage_val = None
            if "vfs.fs.size[/,pused]" in host_items:
                storage_itemid = str(host_items["vfs.fs.size[/,pused]"].get("itemid", ""))
                storage_val = history_values.get(storage_itemid)

            os_detected = inv.get("os_full") or inv.get("os")
            if not os_detected and "system.sw.os" in host_items:
                os_detected = host_items["system.sw.os"].get("name")
            if not os_detected and "system.uname" in host_items:
                os_detected = host_items["system.uname"].get("name")

            result.append({
                "hostid": hid,
                "host": h.get("host", ""),
                "name": h.get("name") or h.get("host", ""),
                "status": h_status,
                "maintenance_status": h.get("maintenance_status", "0"),
                "interfaces": h.get("interfaces", []),
                "groups": groups,
                "inventory": inv,
                "tags": h.get("tags", []),
                "metrics": {
                    "cpu_util": cpu_val,
                    "memory_util": mem_val,
                    "storage_util": storage_val
                },
                "os": os_detected or "Unknown OS",
                "hardware": inv.get("hardware") or "Standard Compute"
            })
        return result

    async def get_problem_count(
        self,
        time_from: Optional[int] = None,
        time_till: Optional[int] = None,
        severities: Optional[List[int]] = None,
        acknowledged: Optional[bool] = None,
        suppressed: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        params: Dict[str, Any] = {
            "countOutput": True,
            "recent": True
        }
        if time_from is not None:
            params["time_from"] = time_from
        if time_till is not None:
            params["time_till"] = time_till
        if severities:
            params["severities"] = severities
        if acknowledged is not None:
            params["acknowledged"] = acknowledged
        if suppressed is not None:
            params["suppressed"] = suppressed
        if search:
            params["search"] = {"name": search}
            params["searchByAny"] = True

        res = await self._call_api("problem.get", params)
        try:
            return int(res)
        except (ValueError, TypeError):
            return 0

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
        valid_sortfields = {"eventid", "clock", "severity", "name"}
        sf = sort_field if sort_field in valid_sortfields else "clock"
        so = "ASC" if sort_order.upper() == "ASC" else "DESC"

        bounded_limit = min(max(limit + offset, 1), 1000)
        params: Dict[str, Any] = {
            "output": [
                "eventid", "source", "object", "objectid", "clock", "ns",
                "r_eventid", "r_clock", "name", "acknowledged", "severity",
                "cause_eventid", "opdata", "suppressed"
            ],
            "selectHosts": ["hostid", "host", "name"],
            "selectTags": ["tag", "value"],
            "selectAcknowledges": ["acknowledgeid", "userid", "clock", "message", "action", "old_severity", "new_severity"],
            "selectSuppressionData": ["maintenanceid", "suppress_until"],
            "recent": True,
            "sortfield": [sf],
            "sortorder": so,
            "limit": bounded_limit
        }
        if time_from is not None:
            params["time_from"] = time_from
        if time_till is not None:
            params["time_till"] = time_till
        if severities:
            params["severities"] = severities
        if acknowledged is not None:
            params["acknowledged"] = acknowledged
        if suppressed is not None:
            params["suppressed"] = suppressed
        if search:
            params["search"] = {"name": search}
            params["searchByAny"] = True

        raw_problems = await self._call_api("problem.get", params) or []
        # Safe client-side pagination slice preserving application contract without unsupported offset
        return raw_problems[offset : offset + limit] if offset > 0 or len(raw_problems) > limit else raw_problems

    async def get_problem_detail(self, event_id: str) -> Optional[Dict[str, Any]]:
        prob_params = {
            "eventids": [event_id],
            "output": [
                "eventid", "source", "object", "objectid", "clock", "ns",
                "r_eventid", "r_clock", "name", "acknowledged", "severity",
                "cause_eventid", "opdata", "suppressed"
            ],
            "selectHosts": ["hostid", "host", "name"],
            "selectTags": ["tag", "value"],
            "selectAcknowledges": ["acknowledgeid", "userid", "clock", "message", "action", "old_severity", "new_severity"],
            "selectSuppressionData": ["maintenanceid", "suppress_until"],
            "recent": True
        }
        raw_prob = await self._call_api("problem.get", prob_params) or []
        if not raw_prob:
            return None

        prob = raw_prob[0]

        alerts = []
        try:
            event_params = {
                "eventids": [event_id],
                "output": ["eventid", "clock", "value", "name", "severity"],
                "selectAlerts": ["alertid", "mediatypeid", "clock", "sendto", "status", "error"]
            }
            raw_event = await self._call_api("event.get", event_params) or []
            if raw_event and raw_event[0].get("alerts"):
                alerts = raw_event[0]["alerts"]
        except Exception:
            pass

        prob["alerts"] = alerts
        return prob

    async def get_slas(
        self,
        sla_ids: Optional[List[str]] = None,
        service_ids: Optional[List[str]] = None,
        search: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        # Zabbix sla.get does not support offset. Bounded limit strictly enforced.
        params: Dict[str, Any] = {
            "output": ["slaid", "name", "period", "slo", "effective_date", "timezone", "status", "description"],
            "selectSchedule": ["period_from", "period_to"],
            "selectExcludedDowntimes": ["name", "period_from", "period_to"],
            "selectServiceTags": ["tag", "operator", "value"],
            "limit": min(max(limit, 1), 500)
        }
        if sla_ids:
            params["slaids"] = sla_ids
        if service_ids:
            params["serviceids"] = service_ids
        if search:
            params["search"] = {"name": search}
            params["searchByAny"] = True

        res = await self._call_api("sla.get", params)
        return res or []

    async def get_sla_sli(
        self,
        slaid: str,
        period_from: Optional[int] = None,
        period_to: Optional[int] = None,
        periods: Optional[int] = None,
        service_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        # Zabbix sla.getsli requires single slaid.
        params: Dict[str, Any] = {
            "slaid": slaid
        }
        if period_from is not None:
            params["period_from"] = period_from
        if period_to is not None:
            params["period_to"] = period_to
        if periods is not None:
            params["periods"] = min(max(periods, 1), 100)
        if service_ids:
            params["serviceids"] = service_ids

        res = await self._call_api("sla.getsli", params)
        return res or {}

    async def get_services(
        self,
        service_ids: Optional[List[str]] = None,
        sla_ids: Optional[List[str]] = None,
        search: Optional[str] = None,
        status: Optional[int] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        # Zabbix service.get does not support offset. Bounded query enforced.
        params: Dict[str, Any] = {
            "output": ["serviceid", "name", "status", "algorithm", "created_at", "description"],
            "selectProblemEvents": ["eventid", "severity", "name"],
            "selectTags": ["tag", "value"],
            "selectStatusRules": ["type", "limit_value", "limit_status", "new_status"],
            "limit": min(max(limit, 1), 1000)
        }
        if service_ids:
            params["serviceids"] = service_ids
        if sla_ids:
            params["slaids"] = sla_ids
        if status is not None:
            params["filter"] = {"status": status}
        if search:
            params["search"] = {"name": search}
            params["searchByAny"] = True

        res = await self._call_api("service.get", params)
        return res or []

    async def get_host_telemetry_history(
        self,
        host_id: str,
        time_from: int,
        time_till: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query real Zabbix 7.0.5 history for CPU, memory, and storage utilization.
        Step 1: Discover itemids for system.cpu.util, vm.memory.util, vfs.fs.size[/,pused].
        Step 2: Query history.get with history=0 (float), time_from, time_till.
        """
        key_map = {
            "system.cpu.util": "cpu",
            "vm.memory.util": "memory",
            "vfs.fs.size[/,pused]": "storage"
        }
        series: Dict[str, List[Dict[str, Any]]] = {
            "cpu": [],
            "memory": [],
            "storage": []
        }

        try:
            items = await self._call_api("item.get", {
                "output": ["itemid", "key_", "value_type"],
                "hostids": [host_id],
                "filter": {
                    "key_": list(key_map.keys())
                }
            }) or []

            item_to_metric: Dict[str, str] = {}
            float_itemids: List[str] = []
            for it in items:
                k = it.get("key_")
                iid = str(it.get("itemid"))
                if k in key_map:
                    metric = key_map[k]
                    item_to_metric[iid] = metric
                    float_itemids.append(iid)

            if float_itemids:
                raw_history = await self._call_api("history.get", {
                    "output": ["itemid", "clock", "value"],
                    "history": 0,
                    "itemids": float_itemids,
                    "time_from": time_from,
                    "time_till": time_till,
                    "sortfield": "clock",
                    "sortorder": "ASC",
                    "limit": 1000
                }) or []

                for entry in raw_history:
                    iid = str(entry.get("itemid"))
                    metric = item_to_metric.get(iid)
                    if metric:
                        clock = int(entry.get("clock", 0))
                        try:
                            val = float(entry.get("value", 0.0))
                        except (ValueError, TypeError):
                            val = None
                        
                        import time
                        iso_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(clock))
                        series[metric].append({
                            "clock": clock,
                            "timestamp_iso": iso_str,
                            "value": round(val, 2) if val is not None else None
                        })
        except Exception:
            pass

        return series

