from datetime import datetime, timezone
import math
from typing import List, Dict, Any, Optional

from app.adapters.zabbix.base import ZabbixAdapterBase
from app.core.logging import get_module_logger
from modules.servers.backend.schemas import (
    ServerItemDTO,
    ServerHardwareDTO,
    ServerMetricValue,
    ServerNetworkInterfaceDTO,
    ServerProblemSummaryDTO,
    ServerListSummaryDTO,
    ServerListResponseDTO,
    ServerDetailResponseDTO,
    ServerFilterParams
)

logger = get_module_logger("servers")


class ServersService:
    """
    Business service for the Servers Module.
    Consumes raw Zabbix inventory and items, applying enterprise normalization,
    evidence-based hardware status evaluation, multi-attribute filtering,
    and server detail drilldown.
    """

    def __init__(self, adapter: ZabbixAdapterBase):
        self.adapter = adapter

    def _normalize_metric(self, val: Optional[float]) -> ServerMetricValue:
        """
        Adheres strictly to the Golden Rules:
        Never fabricate 0% or 100% when telemetry is absent.
        """
        if val is None:
            return ServerMetricValue(
                value=None,
                formatted="NO_DATA",
                status="NO_DATA",
                unit="%"
            )
        try:
            num = float(val)
            status = "NORMAL"
            if num >= 90.0:
                status = "CRITICAL"
            elif num >= 70.0:
                status = "WARNING"

            return ServerMetricValue(
                value=round(num, 1),
                formatted=f"{num:.1f}%",
                status=status,
                unit="%"
            )
        except (ValueError, TypeError):
            return ServerMetricValue(
                value=None,
                formatted="NO_DATA",
                status="NO_DATA",
                unit="%"
            )

    def _detect_os_type(self, os_name: str) -> str:
        s = os_name.lower()
        if any(k in s for k in ("linux", "ubuntu", "debian", "centos", "rhel", "red hat", "rocky", "fedora", "alpine", "suse")):
            return "linux"
        if "windows" in s:
            return "windows"
        if any(k in s for k in ("cisco", "vyos", "router", "switch", "juniper", "arista", "fortinet", "firewall", "pfsense")):
            return "network"
        return "other"

    async def get_servers(self, filters: ServerFilterParams) -> ServerListResponseDTO:
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Fetch raw inventory records and problems
        raw_servers = await self.adapter.get_server_inventory(limit=1000)
        raw_problems = await self.adapter.get_problems(limit=500)

        # 2. Map problems by hostid and hostname
        problems_by_host: Dict[str, List[Any]] = {}
        for p in raw_problems:
            if p.host_id:
                problems_by_host.setdefault(str(p.host_id), []).append(p)
            if p.host_name:
                problems_by_host.setdefault(p.host_name.upper(), []).append(p)

        # 3. Transform and normalize each server
        all_items: List[ServerItemDTO] = []
        for s in raw_servers:
            hid = str(s.get("hostid", ""))
            hname = s.get("name") or s.get("host") or f"Host-{hid}"
            tech_name = s.get("host") or hname

            # Interfaces
            interfaces: List[ServerNetworkInterfaceDTO] = []
            primary_ip = ""
            main_available = "UNKNOWN"

            raw_interfaces = s.get("interfaces", [])
            for rif in raw_interfaces:
                type_int = int(rif.get("type", 1))
                type_map = {1: "AGENT", 2: "SNMP", 3: "IPMI", 4: "JMX"}
                type_str = type_map.get(type_int, "AGENT")

                avail_int = int(rif.get("available", 0))
                avail_str = "UNKNOWN"
                if avail_int == 1:
                    avail_str = "AVAILABLE"
                elif avail_int == 2:
                    avail_str = "UNAVAILABLE"

                is_main = bool(int(rif.get("main", 1 if not interfaces else 0)))
                ip_addr = rif.get("ip", "")
                if is_main and not primary_ip:
                    primary_ip = ip_addr
                    main_available = avail_str

                interfaces.append(ServerNetworkInterfaceDTO(
                    interfaceid=str(rif.get("interfaceid", "")),
                    ip=ip_addr,
                    dns=rif.get("dns", ""),
                    port=str(rif.get("port", "10050")),
                    type=type_str,
                    is_main=is_main,
                    availability=avail_str,
                    error=rif.get("error") or None
                ))

            if not primary_ip and interfaces:
                primary_ip = interfaces[0].ip
                main_available = interfaces[0].availability

            # Tags and metadata
            tags = s.get("tags") or []
            dc = None
            rack = None
            env = None
            for t in tags:
                tag_k = t.get("tag", "").lower()
                tag_v = t.get("value", "")
                if tag_k in ("datacenter", "dc", "site") and not dc:
                    dc = tag_v
                elif tag_k in ("rack", "cabinet") and not rack:
                    rack = tag_v
                elif tag_k in ("environment", "env") and not env:
                    env = tag_v

            inv = s.get("inventory") or {}
            if not dc and inv.get("location"):
                dc = inv.get("location")
            if not rack and inv.get("site_rack"):
                rack = inv.get("site_rack")

            # Metrics
            raw_metrics = s.get("metrics") or {}
            hardware = ServerHardwareDTO(
                cpu_utilization=self._normalize_metric(raw_metrics.get("cpu_util")),
                cpu_cores=raw_metrics.get("cpu_cores"),
                cpu_load=raw_metrics.get("cpu_load"),
                memory_utilization=self._normalize_metric(raw_metrics.get("memory_util")),
                memory_total_bytes=raw_metrics.get("memory_total"),
                memory_used_bytes=raw_metrics.get("memory_used"),
                storage_utilization=self._normalize_metric(raw_metrics.get("storage_util")),
                storage_total_bytes=raw_metrics.get("storage_total"),
                storage_used_bytes=raw_metrics.get("storage_used")
            )

            # Problem summary
            host_probs = problems_by_host.get(hid, []) or problems_by_host.get(hname.upper(), [])
            sev_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            highest_sev = None
            for p in host_probs:
                sev = getattr(p, "severity", 0)
                if sev in sev_counts:
                    sev_counts[sev] += 1
                if highest_sev is None or sev > highest_sev:
                    highest_sev = sev

            problem_summary = ServerProblemSummaryDTO(
                total=len(host_probs),
                disaster=sev_counts[5],
                high=sev_counts[4],
                average=sev_counts[3],
                warning=sev_counts[2],
                information=sev_counts[1],
                highest_severity=highest_sev
            )

            os_full = s.get("os") or inv.get("os_full") or inv.get("os") or "Unknown OS"
            os_type = self._detect_os_type(os_full)

            item = ServerItemDTO(
                id=hid,
                name=hname,
                technical_name=tech_name,
                status=s.get("status", "UP"),
                overall_availability=main_available,
                ip=primary_ip,
                os=os_full,
                os_type=os_type,
                hardware_summary=s.get("hardware") or inv.get("hardware") or "Standard Compute",
                hardware=hardware,
                interfaces=interfaces,
                groups=s.get("groups", []),
                tags=tags,
                datacenter=dc,
                rack=rack,
                environment=env,
                maintenance_name="Scheduled Maintenance" if s.get("status") == "MAINTENANCE" else None,
                problems=problem_summary,
                last_updated=now_iso,
                data_lineage={
                    "host": "Zabbix host.get",
                    "interfaces": "Zabbix selectInterfaces",
                    "inventory": "Zabbix selectInventory",
                    "telemetry": "Zabbix item.get (lastvalue)"
                }
            )
            all_items.append(item)

        # 4. Filter pipeline
        filtered = all_items

        if filters.search:
            q = filters.search.strip().lower()
            filtered = [
                x for x in filtered
                if q in x.name.lower()
                or q in x.technical_name.lower()
                or q in x.ip.lower()
                or q in x.os.lower()
                or (x.datacenter and q in x.datacenter.lower())
                or (x.rack and q in x.rack.lower())
                or any(q in t.get("value", "").lower() for t in x.tags)
            ]

        if filters.group:
            g_low = filters.group.lower()
            filtered = [x for x in filtered if any(g_low in g.lower() for g in x.groups)]

        if filters.status:
            filtered = [x for x in filtered if x.status.upper() == filters.status.upper()]

        if filters.availability:
            filtered = [x for x in filtered if x.overall_availability.upper() == filters.availability.upper()]

        if filters.os_type:
            filtered = [x for x in filtered if x.os_type.lower() == filters.os_type.lower()]

        if filters.datacenter:
            dc_low = filters.datacenter.lower()
            filtered = [x for x in filtered if x.datacenter and dc_low in x.datacenter.lower()]

        if filters.has_problems is not None:
            if filters.has_problems:
                filtered = [x for x in filtered if x.problems.total > 0]
            else:
                filtered = [x for x in filtered if x.problems.total == 0]

        if filters.severity is not None:
            filtered = [x for x in filtered if x.problems.highest_severity and x.problems.highest_severity >= filters.severity]

        # 5. Calculate summary over filtered collection
        total_servers = len(filtered)
        up_count = sum(1 for x in filtered if x.status == "UP")
        down_count = sum(1 for x in filtered if x.status == "DOWN")
        maint_count = sum(1 for x in filtered if x.status == "MAINTENANCE")
        avail_count = sum(1 for x in filtered if x.overall_availability == "AVAILABLE")
        unavail_count = sum(1 for x in filtered if x.overall_availability == "UNAVAILABLE")
        unknown_count = sum(1 for x in filtered if x.overall_availability == "UNKNOWN")

        cpu_vals = [x.hardware.cpu_utilization.value for x in filtered if x.hardware.cpu_utilization.value is not None]
        mem_vals = [x.hardware.memory_utilization.value for x in filtered if x.hardware.memory_utilization.value is not None]
        stor_vals = [x.hardware.storage_utilization.value for x in filtered if x.hardware.storage_utilization.value is not None]

        summary = ServerListSummaryDTO(
            total_servers=total_servers,
            servers_up=up_count,
            servers_down=down_count,
            servers_maintenance=maint_count,
            available_count=avail_count,
            unavailable_count=unavail_count,
            unknown_count=unknown_count,
            avg_cpu_percent=round(sum(cpu_vals) / len(cpu_vals), 1) if cpu_vals else None,
            avg_memory_percent=round(sum(mem_vals) / len(mem_vals), 1) if mem_vals else None,
            avg_storage_percent=round(sum(stor_vals) / len(stor_vals), 1) if stor_vals else None
        )

        # 6. Sorting
        def get_sort_key(item: ServerItemDTO):
            field = filters.sort_by.lower()
            if field == "name":
                return item.name.lower()
            if field == "status":
                return item.status
            if field == "ip":
                return item.ip
            if field == "cpu":
                return item.hardware.cpu_utilization.value if item.hardware.cpu_utilization.value is not None else -1.0
            if field == "memory":
                return item.hardware.memory_utilization.value if item.hardware.memory_utilization.value is not None else -1.0
            if field == "storage":
                return item.hardware.storage_utilization.value if item.hardware.storage_utilization.value is not None else -1.0
            if field == "problems":
                return item.problems.total
            return item.name.lower()

        reverse = (filters.sort_order.lower() == "desc")
        filtered.sort(key=get_sort_key, reverse=reverse)

        # 7. Pagination
        page_size = max(1, min(filters.page_size, 100))
        total_pages = max(1, math.ceil(total_servers / page_size)) if total_servers > 0 else 1
        page = max(1, min(filters.page, total_pages))

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_items = filtered[start_idx:end_idx]

        return ServerListResponseDTO(
            items=paged_items,
            total_count=total_servers,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            summary=summary,
            applied_filters=filters.model_dump(exclude_none=True),
            generated_at=now_iso
        )

    async def get_server_by_id(self, server_id: str) -> Optional[ServerDetailResponseDTO]:
        now_iso = datetime.now(timezone.utc).isoformat()
        # Query list without pagination constraints
        res = await self.get_servers(ServerFilterParams(page=1, page_size=100))
        found = next((x for x in res.items if x.id == server_id), None)
        if not found:
            return None

        # Fetch problem details for this host
        raw_problems = await self.adapter.get_problems(limit=50)
        host_probs = [
            {
                "eventid": p.eventid,
                "name": p.name,
                "severity": p.severity,
                "clock": p.clock,
                "acknowledged": p.acknowledged
            }
            for p in raw_problems
            if (p.host_id and p.host_id == server_id) or (p.host_name and p.host_name.upper() == found.name.upper())
        ]

        return ServerDetailResponseDTO(
            server=found,
            inventory={
                "hardware": found.hardware_summary,
                "os": found.os,
                "datacenter": found.datacenter or "Unassigned",
                "rack": found.rack or "Unassigned",
                "environment": found.environment or "Unassigned"
            },
            active_problems=host_probs,
            metrics_breakdown={
                "cpu": found.hardware.cpu_utilization.model_dump(),
                "memory": found.hardware.memory_utilization.model_dump(),
                "storage": found.hardware.storage_utilization.model_dump()
            },
            generated_at=now_iso
        )
