from datetime import datetime, timezone
import math
import time
from typing import List, Dict, Any, Optional

from app.adapters.zabbix.base import ZabbixAdapterBase
from app.core.logging import get_module_logger
from modules.host360.backend.schemas import (
    HostMetricValueDTO,
    HostHardwareTelemetryDTO,
    HostInterfaceDTO,
    HostProblemEventDTO,
    Host360ListItemDTO,
    Host360ListResponseDTO,
    Host360DetailDTO,
    TelemetrySeriesPointDTO,
    Host360TelemetryResponseDTO
)

logger = get_module_logger("host360")


class Host360Service:
    """
    Business service for Module 05: Host 360.
    Provides 360-degree host telemetry, time-series history metrics,
    hardware telemetry, network interfaces, inventory, and active event overlays.
    Adheres strictly to the Zero Fabrication Policy: never invents fake metrics or SLA values.
    """

    def __init__(self, adapter: ZabbixAdapterBase):
        self.adapter = adapter

    def _normalize_metric(self, val: Optional[float], unit: str = "%") -> HostMetricValueDTO:
        if val is None:
            return HostMetricValueDTO(
                value=None,
                formatted="NO_DATA",
                status="NO_DATA",
                unit=unit
            )
        try:
            num = float(val)
            status = "NORMAL"
            if num >= 90.0:
                status = "CRITICAL"
            elif num >= 70.0:
                status = "WARNING"

            return HostMetricValueDTO(
                value=round(num, 1),
                formatted=f"{num:.1f}{unit}",
                status=status,
                unit=unit
            )
        except (ValueError, TypeError):
            return HostMetricValueDTO(
                value=None,
                formatted="NO_DATA",
                status="NO_DATA",
                unit=unit
            )

    async def list_hosts(
        self,
        search: Optional[str] = None,
        group: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Host360ListResponseDTO:
        now_iso = datetime.now(timezone.utc).isoformat()

        # Query authoritative server inventory from adapter
        raw_servers = await self.adapter.get_server_inventory(limit=1000)
        raw_problems = await self.adapter.get_problems(limit=500)

        # Index active problems by hostid and hostname
        prob_count_by_host: Dict[str, int] = {}
        for p in raw_problems:
            if p.host_id:
                hid = str(p.host_id)
                prob_count_by_host[hid] = prob_count_by_host.get(hid, 0) + 1
            if p.host_name:
                hn = p.host_name.upper()
                prob_count_by_host[hn] = prob_count_by_host.get(hn, 0) + 1

        items: List[Host360ListItemDTO] = []
        for s in raw_servers:
            hid = str(s.get("hostid", ""))
            hname = s.get("name") or s.get("host") or f"Host-{hid}"
            tech_name = s.get("host") or hname

            # Interfaces
            interfaces: List[HostInterfaceDTO] = []
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

                interfaces.append(HostInterfaceDTO(
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

            tags = s.get("tags") or []
            dc = None
            rack = None
            for t in tags:
                tk = t.get("tag", "").lower()
                tv = t.get("value", "")
                if tk in ("datacenter", "dc", "site") and not dc:
                    dc = tv
                elif tk in ("rack", "cabinet") and not rack:
                    rack = tv

            inv = s.get("inventory") or {}
            if not dc and inv.get("location"):
                dc = inv.get("location")
            if not rack and inv.get("site_rack"):
                rack = inv.get("site_rack")

            raw_metrics = s.get("metrics") or {}
            cpu_val = raw_metrics.get("cpu_util")
            mem_val = raw_metrics.get("memory_util")
            stor_val = raw_metrics.get("storage_util")

            active_cnt = prob_count_by_host.get(hid, 0)
            if active_cnt == 0:
                active_cnt = prob_count_by_host.get(hname.upper(), 0)

            os_full = s.get("os") or inv.get("os_full") or inv.get("os")

            items.append(Host360ListItemDTO(
                host_id=hid,
                name=hname,
                technical_name=tech_name,
                status=s.get("status", "UP"),
                availability=main_available,
                primary_ip=primary_ip,
                groups=s.get("groups", []),
                datacenter=dc,
                rack=rack,
                os=os_full,
                active_problems_count=active_cnt,
                cpu_util=round(float(cpu_val), 1) if cpu_val is not None else None,
                memory_util=round(float(mem_val), 1) if mem_val is not None else None,
                storage_util=round(float(stor_val), 1) if stor_val is not None else None,
                interfaces=interfaces
            ))

        # Filter
        filtered = items
        if search:
            q = search.strip().lower()
            filtered = [
                x for x in filtered
                if q in x.name.lower()
                or q in x.technical_name.lower()
                or q in x.primary_ip.lower()
                or (x.os and q in x.os.lower())
                or (x.datacenter and q in x.datacenter.lower())
            ]

        if group:
            g_low = group.strip().lower()
            filtered = [x for x in filtered if any(g_low in g.lower() for g in x.groups)]

        total_count = len(filtered)
        page_size_safe = max(1, min(page_size, 100))
        total_pages = max(1, math.ceil(total_count / page_size_safe)) if total_count > 0 else 1
        page_safe = max(1, min(page, total_pages))

        start_idx = (page_safe - 1) * page_size_safe
        end_idx = start_idx + page_size_safe
        paged_items = filtered[start_idx:end_idx]

        return Host360ListResponseDTO(
            items=paged_items,
            total_count=total_count,
            page=page_safe,
            page_size=page_size_safe,
            total_pages=total_pages,
            generated_at=now_iso
        )

    async def get_host_360_detail(self, host_id: str) -> Optional[Host360DetailDTO]:
        now_iso = datetime.now(timezone.utc).isoformat()

        raw_servers = await self.adapter.get_server_inventory(limit=1000)
        found = next((s for s in raw_servers if str(s.get("hostid")) == host_id), None)
        if not found:
            return None

        hname = found.get("name") or found.get("host") or f"Host-{host_id}"
        tech_name = found.get("host") or hname

        # Interfaces
        interfaces: List[HostInterfaceDTO] = []
        primary_ip = ""
        main_available = "UNKNOWN"

        raw_interfaces = found.get("interfaces", [])
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

            interfaces.append(HostInterfaceDTO(
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
            main_available = interfaces[0].availability

        # Hardware metrics
        raw_metrics = found.get("metrics") or {}
        telemetry = HostHardwareTelemetryDTO(
            cpu_utilization=self._normalize_metric(raw_metrics.get("cpu_util")),
            cpu_cores=raw_metrics.get("cpu_cores"),
            cpu_load_1m=raw_metrics.get("cpu_load"),
            memory_utilization=self._normalize_metric(raw_metrics.get("memory_util")),
            memory_total_bytes=raw_metrics.get("memory_total"),
            memory_used_bytes=raw_metrics.get("memory_used"),
            storage_utilization=self._normalize_metric(raw_metrics.get("storage_util")),
            storage_total_bytes=raw_metrics.get("storage_total"),
            storage_used_bytes=raw_metrics.get("storage_used")
        )

        # Inventory
        inv = found.get("inventory") or {}
        tags = found.get("tags") or []

        # Active problems
        raw_problems = await self.adapter.get_problems(limit=100)
        sev_map = {1: "Information", 2: "Warning", 3: "Average", 4: "High", 5: "Disaster"}
        host_problems: List[HostProblemEventDTO] = []
        for p in raw_problems:
            if (p.host_id and str(p.host_id) == host_id) or (p.host_name and p.host_name.upper() == hname.upper()):
                host_problems.append(HostProblemEventDTO(
                    eventid=str(p.eventid),
                    name=p.name,
                    severity=p.severity,
                    severity_name=sev_map.get(p.severity, "Unknown"),
                    clock=p.clock,
                    acknowledged=p.acknowledged,
                    opdata=p.opdata if hasattr(p, "opdata") else None
                ))

        # Maintenance
        maint = None
        if found.get("status") == "MAINTENANCE" or found.get("maintenance_status") == "1":
            maint = {
                "active": True,
                "name": "Scheduled Maintenance Window"
            }

        return Host360DetailDTO(
            host_id=host_id,
            name=hname,
            technical_name=tech_name,
            status=found.get("status", "UP"),
            overall_availability=main_available,
            groups=found.get("groups", []),
            interfaces=interfaces,
            telemetry=telemetry,
            inventory=inv,
            tags=tags,
            active_problems=host_problems,
            maintenance=maint,
            data_lineage={
                "host": "Zabbix host.get",
                "interfaces": "Zabbix selectInterfaces",
                "inventory": "Zabbix selectInventory",
                "telemetry": "Zabbix item.get / history.get",
                "problems": "Zabbix problem.get"
            },
            generated_at=now_iso
        )

    async def get_host_telemetry_series(
        self,
        host_id: str,
        time_range: str = "24h"
    ) -> Optional[Host360TelemetryResponseDTO]:
        now_ts = int(time.time())
        range_seconds = {
            "1h": 3600,
            "6h": 21600,
            "12h": 43200,
            "24h": 86400,
            "7d": 604800,
            "30d": 2592000
        }
        duration = range_seconds.get(time_range, 86400)
        time_from = now_ts - duration
        time_till = now_ts

        # Verify host exists
        detail = await self.get_host_360_detail(host_id)
        if not detail:
            return None

        # Fetch series from adapter
        series_dict = await self.adapter.get_host_telemetry_history(
            host_id=host_id,
            time_from=time_from,
            time_till=time_till
        )

        formatted_series: Dict[str, List[TelemetrySeriesPointDTO]] = {}
        for metric_name, points in series_dict.items():
            formatted_series[metric_name] = [
                TelemetrySeriesPointDTO(
                    clock=pt.get("clock", 0),
                    timestamp_iso=pt.get("timestamp_iso", ""),
                    value=pt.get("value")
                )
                for pt in points
            ]

        return Host360TelemetryResponseDTO(
            host_id=host_id,
            host_name=detail.name,
            time_range=time_range,
            time_from=time_from,
            time_till=time_till,
            series=formatted_series,
            generated_at=datetime.now(timezone.utc).isoformat()
        )
