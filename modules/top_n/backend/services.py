from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.adapters.zabbix.base import ZabbixAdapterBase
from app.core.logging import get_module_logger
from modules.top_n.backend.schemas import (
    TopNMetricValueDTO,
    TopNItemDTO,
    TopNResponseDTO,
    TopNOverviewResponseDTO
)

logger = get_module_logger("top_n")


class TopNService:
    """
    Business service for Module 06: Top N.
    Provides ranked resource utilization across enterprise infrastructure for:
    - CPU utilization (%)
    - Memory utilization (%)
    - Storage utilization (%)
    - Active problems (incident count)
    Adheres strictly to the Zero Fabrication Policy: never invents fake metrics or SLA values.
    """

    def __init__(self, adapter: ZabbixAdapterBase):
        self.adapter = adapter

    def _normalize_metric(self, val: Optional[float], unit: str = "%") -> TopNMetricValueDTO:
        if val is None:
            return TopNMetricValueDTO(
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

            return TopNMetricValueDTO(
                value=round(num, 1),
                formatted=f"{num:.1f}{unit}",
                status=status,
                unit=unit
            )
        except (ValueError, TypeError):
            return TopNMetricValueDTO(
                value=None,
                formatted="NO_DATA",
                status="NO_DATA",
                unit=unit
            )

    async def get_rankings(
        self,
        metric: str = "cpu",
        limit: int = 10,
        order: str = "desc",
        group: Optional[str] = None
    ) -> TopNResponseDTO:
        now_iso = datetime.now(timezone.utc).isoformat()

        # Fetch authoritative server inventory and active problems
        raw_servers = await self.adapter.get_server_inventory(limit=1000)
        raw_problems = await self.adapter.get_problems(limit=500)

        # Index problems by hostid and hostname
        prob_count_by_host: Dict[str, int] = {}
        highest_sev_by_host: Dict[str, int] = {}
        for p in raw_problems:
            hid = str(p.host_id) if p.host_id else None
            hname = p.host_name.upper() if p.host_name else None
            sev = getattr(p, "severity", 0)

            if hid:
                prob_count_by_host[hid] = prob_count_by_host.get(hid, 0) + 1
                if hid not in highest_sev_by_host or sev > highest_sev_by_host[hid]:
                    highest_sev_by_host[hid] = sev
            if hname:
                prob_count_by_host[hname] = prob_count_by_host.get(hname, 0) + 1
                if hname not in highest_sev_by_host or sev > highest_sev_by_host[hname]:
                    highest_sev_by_host[hname] = sev

        # Filter by host group if requested
        candidate_servers = raw_servers
        if group:
            g_low = group.strip().lower()
            candidate_servers = [
                s for s in candidate_servers
                if any(g_low in g.lower() for g in s.get("groups", []))
            ]

        items_with_metric: List[Dict[str, Any]] = []

        metric_display_map = {
            "cpu": "CPU Utilization",
            "memory": "Memory Utilization",
            "storage": "Storage Utilization",
            "problems": "Active Incidents Count"
        }
        metric_display = metric_display_map.get(metric, metric.upper())

        for s in candidate_servers:
            hid = str(s.get("hostid", ""))
            hname = s.get("name") or s.get("host") or f"Host-{hid}"
            tech_name = s.get("host") or hname

            # Primary IP & availability
            primary_ip = ""
            main_available = "UNKNOWN"
            raw_interfaces = s.get("interfaces", [])
            for rif in raw_interfaces:
                avail_int = int(rif.get("available", 0))
                avail_str = "AVAILABLE" if avail_int == 1 else "UNAVAILABLE" if avail_int == 2 else "UNKNOWN"
                is_main = bool(int(rif.get("main", 1 if not primary_ip else 0)))
                ip_addr = rif.get("ip", "")
                if is_main and not primary_ip:
                    primary_ip = ip_addr
                    main_available = avail_str

            if not primary_ip and raw_interfaces:
                primary_ip = raw_interfaces[0].get("ip", "")
                main_available = "AVAILABLE" if raw_interfaces[0].get("available") == 1 else "UNKNOWN"

            # Problems count
            active_cnt = prob_count_by_host.get(hid, 0)
            if active_cnt == 0 and hname.upper() in prob_count_by_host:
                active_cnt = prob_count_by_host[hname.upper()]

            high_sev = highest_sev_by_host.get(hid)
            if high_sev is None and hname.upper() in highest_sev_by_host:
                high_sev = highest_sev_by_host[hname.upper()]

            raw_metrics = s.get("metrics") or {}

            # Extract metric value according to requested dimension
            raw_num: Optional[float] = None
            if metric == "cpu":
                raw_num = raw_metrics.get("cpu_util")
            elif metric == "memory":
                raw_num = raw_metrics.get("memory_util")
            elif metric == "storage":
                raw_num = raw_metrics.get("storage_util")
            elif metric == "problems":
                raw_num = float(active_cnt)

            num_float: Optional[float] = None
            if raw_num is not None:
                try:
                    num_float = float(raw_num)
                except (ValueError, TypeError):
                    num_float = None

            unit = " problems" if metric == "problems" else "%"
            metric_val_dto = self._normalize_metric(num_float, unit=unit)
            if metric == "problems" and num_float is not None:
                metric_val_dto.formatted = f"{int(num_float)} incidents"
                metric_val_dto.status = "CRITICAL" if num_float >= 5 else "WARNING" if num_float >= 1 else "NORMAL"

            items_with_metric.append({
                "host_id": hid,
                "host_name": hname,
                "technical_name": tech_name,
                "primary_ip": primary_ip,
                "status": s.get("status", "UP"),
                "availability": main_available,
                "groups": s.get("groups", []),
                "metric_name": metric,
                "metric_value": metric_val_dto,
                "raw_value": num_float,
                "active_problems_count": active_cnt,
                "highest_severity": high_sev,
                "tags": s.get("tags", [])
            })

        # Sorting logic:
        # For ranking, hosts with valid telemetry appear first in order.
        # Hosts with NO_DATA sort after valid hosts when desc, or last when asc.
        is_reverse = (order.lower() == "desc")

        def sort_key(item: Dict[str, Any]):
            val = item["raw_value"]
            if val is None:
                # Put None at the bottom
                return -float("inf") if is_reverse else float("inf")
            return val

        items_with_metric.sort(key=sort_key, reverse=is_reverse)

        # Assign ranks
        ranked_items: List[TopNItemDTO] = []
        limit_safe = max(1, min(limit, 100))
        for idx, it in enumerate(items_with_metric[:limit_safe], start=1):
            ranked_items.append(TopNItemDTO(
                rank=idx,
                host_id=it["host_id"],
                host_name=it["host_name"],
                technical_name=it["technical_name"],
                primary_ip=it["primary_ip"],
                status=it["status"],
                availability=it["availability"],
                groups=it["groups"],
                metric_name=it["metric_name"],
                metric_value=it["metric_value"],
                raw_value=it["raw_value"],
                active_problems_count=it["active_problems_count"],
                highest_severity=it["highest_severity"],
                tags=it["tags"]
            ))

        is_truncated = len(raw_servers) >= 1000
        truncation_reason = (
            "Target environment exceeds 1000 hosts. Candidate inventory capped at 1000 nodes for memory safety. "
            "Use targeted host group filters for specific cluster rankings."
            if is_truncated
            else None
        )

        return TopNResponseDTO(
            metric=metric,
            metric_display_name=metric_display,
            order=order.lower(),
            items=ranked_items,
            total_evaluated_hosts=len(candidate_servers),
            is_truncated=is_truncated,
            truncation_reason=truncation_reason,
            generated_at=now_iso
        )

    async def get_overview(self, limit: int = 5, group: Optional[str] = None) -> TopNOverviewResponseDTO:
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Parallel or batched rankings for the 4 core dimensions
        cpu_res = await self.get_rankings(metric="cpu", limit=limit, order="desc", group=group)
        mem_res = await self.get_rankings(metric="memory", limit=limit, order="desc", group=group)
        stor_res = await self.get_rankings(metric="storage", limit=limit, order="desc", group=group)
        prob_res = await self.get_rankings(metric="problems", limit=limit, order="desc", group=group)

        return TopNOverviewResponseDTO(
            cpu=cpu_res.items,
            memory=mem_res.items,
            storage=stor_res.items,
            problems=prob_res.items,
            total_evaluated_hosts=cpu_res.total_evaluated_hosts,
            is_truncated=cpu_res.is_truncated,
            truncation_reason=cpu_res.truncation_reason,
            generated_at=now_iso
        )
