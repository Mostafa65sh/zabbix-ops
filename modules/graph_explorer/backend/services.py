from datetime import datetime, timezone
import time
from typing import List, Dict, Any, Optional

from app.adapters.zabbix.base import ZabbixAdapterBase
from app.core.logging import get_module_logger
from modules.graph_explorer.backend.schemas import (
    GraphPointDTO,
    GraphMetricSeriesDTO,
    MultiSeriesGraphResponseDTO,
    GraphTargetDTO,
    GraphTargetsResponseDTO
)

logger = get_module_logger("graph_explorer")

METRIC_LABELS = {
    "cpu": "CPU Utilization",
    "memory": "Memory Utilization",
    "storage": "Storage Utilization"
}

METRIC_COLORS = {
    "cpu": "#38bdf8",
    "memory": "#a855f7",
    "storage": "#3b82f6"
}


class GraphExplorerService:
    """
    Business service for Module 07: Graph Explorer.
    Provides interactive multi-series metric visualization and cross-host comparison.
    Adheres strictly to the Zero-Fabrication Policy: missing data is represented as None.
    """

    def __init__(self, adapter: ZabbixAdapterBase):
        self.adapter = adapter

    async def get_targets(self, search: Optional[str] = None, group: Optional[str] = None) -> GraphTargetsResponseDTO:
        now_iso = datetime.now(timezone.utc).isoformat()
        raw_servers = await self.adapter.get_server_inventory(limit=1000)

        targets: List[GraphTargetDTO] = []
        for s in raw_servers:
            hid = str(s.get("hostid", ""))
            hname = s.get("name") or s.get("host") or f"Host-{hid}"
            tech_name = s.get("host") or hname

            primary_ip = ""
            raw_interfaces = s.get("interfaces", [])
            for rif in raw_interfaces:
                if rif.get("ip"):
                    primary_ip = rif.get("ip")
                    break

            groups = s.get("groups", [])
            if group:
                g_low = group.strip().lower()
                if not any(g_low in g.lower() for g in groups):
                    continue

            if search:
                q = search.strip().lower()
                if not (q in hname.lower() or q in tech_name.lower() or q in primary_ip.lower()):
                    continue

            targets.append(GraphTargetDTO(
                host_id=hid,
                host_name=hname,
                technical_name=tech_name,
                primary_ip=primary_ip,
                status=s.get("status", "UP"),
                groups=groups,
                available_metrics=["cpu", "memory", "storage"]
            ))

        is_truncated = len(raw_servers) >= 1000
        truncation_reason = (
            "Target environment exceeds 1000 hosts. Candidate hosts capped at 1000 nodes for memory safety. "
            "Use search or group filters for specific host targets."
            if is_truncated
            else None
        )

        return GraphTargetsResponseDTO(
            targets=targets,
            total_targets=len(targets),
            is_truncated=is_truncated,
            truncation_reason=truncation_reason,
            generated_at=now_iso
        )

    async def get_multi_series(
        self,
        host_ids: List[str],
        metrics: List[str],
        time_range: str = "24h"
    ) -> MultiSeriesGraphResponseDTO:
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

        # Host inventory to resolve names
        raw_servers = await self.adapter.get_server_inventory(limit=1000)
        servers_map = {str(s.get("hostid")): s for s in raw_servers}

        series_list: List[GraphMetricSeriesDTO] = []

        # Color palette for distinct series lines
        palette = [
            "#38bdf8", "#a855f7", "#3b82f6", "#10b981", "#f59e0b",
            "#ec4899", "#6366f1", "#14b8a6", "#f97316", "#8b5cf6"
        ]
        color_idx = 0

        # Query history for each selected host (bounded O(H) where H <= 10)
        safe_host_ids = host_ids[:10]  # Cap concurrent multi-host comparison to 10 hosts
        valid_metrics = [m for m in metrics if m in ("cpu", "memory", "storage")]

        for hid in safe_host_ids:
            server_info = servers_map.get(hid)
            if not server_info:
                # Host does not exist in monitored inventory; do not query or fabricate telemetry
                continue

            hname = server_info.get("name") or server_info.get("host") or f"Host-{hid}"

            # Query adapter history
            history_data = await self.adapter.get_host_telemetry_history(
                host_id=hid,
                time_from=time_from,
                time_till=time_till
            )

            for m in valid_metrics:
                raw_points = history_data.get(m, [])
                points: List[GraphPointDTO] = []
                values: List[float] = []

                for pt in raw_points:
                    v = pt.get("value")
                    val_float = float(v) if v is not None else None
                    if val_float is not None:
                        values.append(val_float)

                    points.append(GraphPointDTO(
                        clock=pt.get("clock", 0),
                        timestamp_iso=pt.get("timestamp_iso", ""),
                        value=val_float
                    ))

                color = palette[color_idx % len(palette)]
                color_idx += 1

                latest = values[-1] if values else None
                min_val = min(values) if values else None
                max_val = max(values) if values else None
                avg_val = round(sum(values) / len(values), 2) if values else None

                series_list.append(GraphMetricSeriesDTO(
                    series_id=f"{hid}:{m}",
                    host_id=hid,
                    host_name=hname,
                    metric_name=m,
                    metric_label=f"{hname} - {METRIC_LABELS.get(m, m.upper())}",
                    unit="%",
                    color=color,
                    points=points,
                    latest_value=latest,
                    min_value=min_val,
                    max_value=max_val,
                    avg_value=avg_val
                ))

        is_truncated = len(raw_servers) >= 1000
        truncation_reason = (
            "Target environment exceeds 1000 hosts. Candidate hosts capped at 1000 nodes for memory safety."
            if is_truncated
            else None
        )

        return MultiSeriesGraphResponseDTO(
            time_range=time_range,
            time_from=time_from,
            time_till=time_till,
            series=series_list,
            total_series=len(series_list),
            is_truncated=is_truncated,
            truncation_reason=truncation_reason,
            generated_at=datetime.now(timezone.utc).isoformat()
        )
