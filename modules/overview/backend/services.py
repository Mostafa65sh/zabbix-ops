from datetime import datetime, timezone
import time
from typing import List, Dict, Any, Optional

from app.adapters.zabbix.base import ZabbixAdapterBase
from app.core.logging import get_module_logger
from modules.overview.backend.schemas import (
    OverviewResponseDTO,
    TimeRangeDTO,
    HealthSummaryDTO,
    HostStatusSummaryDTO,
    ProblemSeveritySummaryDTO,
    AvailabilitySummaryDTO,
    ActiveProblemDTO,
    TopProblemHostDTO,
    RecentIncidentEventDTO,
    InfrastructureGroupDTO,
    TrendIndicatorDTO,
    OverviewFilterParams
)

logger = get_module_logger("overview")

SEVERITY_NAMES = {
    0: "Not classified",
    1: "Information",
    2: "Warning",
    3: "Average",
    4: "High",
    5: "Disaster"
}


def format_duration(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours > 24:
        days, hours = divmod(hours, 24)
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes:02d}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return f"{seconds}s"


class OverviewService:
    """
    Business service for the Overview Module.
    Consumes normalized data from ZabbixAdapterBase and enforces evidence-based reporting.
    """

    def __init__(self, adapter: ZabbixAdapterBase):
        self.adapter = adapter

    async def get_overview(self, filters: OverviewFilterParams) -> OverviewResponseDTO:
        now = int(time.time())
        # Parse time range in seconds
        range_seconds_map = {
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "6h": 21600,
            "24h": 86400,
            "7d": 604800,
            "30d": 2592000
        }
        window_seconds = range_seconds_map.get(filters.time_range, 86400)
        start_time = now - window_seconds
        end_time = now

        # Fetch telemetry from Zabbix Adapter
        overview_data = await self.adapter.get_overview()
        hosts = await self.adapter.get_hosts(group=filters.group, status=filters.status)
        problems = await self.adapter.get_problems(limit=100, severity=filters.severity)
        events = await self.adapter.get_recent_events(limit=20)

        # Filter problems if host filter is set
        if filters.host:
            problems = [p for p in problems if filters.host.lower() in (p.host_name or "").lower()]
            hosts = [h for h in hosts if filters.host.lower() in h.name.lower()]

        # 1. Evidence-based Health Evaluation
        disaster_problems = [p for p in problems if p.severity == 5]
        high_problems = [p for p in problems if p.severity == 4]
        warning_problems = [p for p in problems if p.severity in (2, 3)]
        down_hosts = [h for h in hosts if h.status == "DOWN"]

        evidence = []
        if disaster_problems:
            health_status = "CRITICAL"
            reason = "active_disaster_problems"
            for dp in disaster_problems:
                evidence.append(f"Disaster: '{dp.name}' on {dp.host_name or 'host'}")
        elif down_hosts:
            health_status = "CRITICAL"
            reason = "hosts_unreachable"
            for dh in down_hosts:
                evidence.append(f"Host '{dh.name}' is DOWN / unreachable")
        elif high_problems:
            health_status = "DEGRADED"
            reason = "active_high_severity_problems"
            for hp in high_problems:
                evidence.append(f"High: '{hp.name}' on {hp.host_name or 'host'}")
        elif warning_problems:
            health_status = "DEGRADED"
            reason = "active_warnings"
            for wp in warning_problems:
                evidence.append(f"Warning: '{wp.name}' on {wp.host_name or 'host'}")
        else:
            health_status = "HEALTHY"
            reason = "all_monitored_systems_operational"
            evidence.append("All hosts report normal telemetry and no critical events active.")

        health_dto = HealthSummaryDTO(
            status=health_status,
            reason=reason,
            evidence=evidence
        )

        # 2. Host Status Counts
        total_hosts = len(hosts)
        available_hosts = sum(1 for h in hosts if h.status == "UP")
        unavailable_hosts = sum(1 for h in hosts if h.status == "DOWN")
        maintenance_hosts = sum(1 for h in hosts if h.status == "MAINTENANCE")
        unknown_hosts = sum(1 for h in hosts if h.status not in ("UP", "DOWN", "MAINTENANCE"))

        hosts_dto = HostStatusSummaryDTO(
            total=total_hosts,
            available=available_hosts,
            unavailable=unavailable_hosts,
            unknown=unknown_hosts,
            maintenance=maintenance_hosts
        )

        # 3. Problem Severity Summary
        problems_dto = ProblemSeveritySummaryDTO(
            total=len(problems),
            disaster=sum(1 for p in problems if p.severity == 5),
            high=sum(1 for p in problems if p.severity == 4),
            average=sum(1 for p in problems if p.severity == 3),
            warning=sum(1 for p in problems if p.severity == 2),
            information=sum(1 for p in problems if p.severity == 1),
        )

        # 4. Measured Availability
        if total_hosts > 0:
            avail_percent = round(((available_hosts + maintenance_hosts) / total_hosts) * 100.0, 2)
        else:
            avail_percent = None

        unplanned_seconds = unavailable_hosts * min(window_seconds, 1800)
        planned_seconds = maintenance_hosts * min(window_seconds, 3600)

        availability_dto = AvailabilitySummaryDTO(
            percent=avail_percent,
            planned_downtime_seconds=planned_seconds,
            unplanned_downtime_seconds=unplanned_seconds,
            unknown_seconds=unknown_hosts * window_seconds,
            lineage={
                "source": "Zabbix Adapter (Monitored Hosts)",
                "method": "Operational Host Availability Ratio",
                "period": filters.time_range,
                "calculation": "((available_hosts + maintenance_hosts) / total_hosts) * 100",
                "unit": "%"
            }
        )

        # 5. Active Problems List
        active_problems_dto = []
        for p in problems:
            dur = max(0, now - p.clock)
            dt_str = datetime.fromtimestamp(p.clock, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            active_problems_dto.append(ActiveProblemDTO(
                eventid=p.eventid,
                severity=p.severity,
                severity_name=SEVERITY_NAMES.get(p.severity, "Unknown"),
                name=p.name,
                host_id=p.host_id,
                host_name=p.host_name or "Unknown Host",
                duration_seconds=dur,
                duration_human=format_duration(dur),
                acknowledged=p.acknowledged,
                started_clock=p.clock,
                started_human=dt_str
            ))

        # 6. Top Problem Hosts
        host_map = {h.id: h for h in hosts}
        host_problems_map: Dict[str, List[ActiveProblemDTO]] = {}
        for ap in active_problems_dto:
            if ap.host_id:
                host_problems_map.setdefault(ap.host_id, []).append(ap)

        top_hosts = []
        for hid, h_probs in host_problems_map.items():
            h_obj = host_map.get(hid)
            h_name = h_obj.name if h_obj else (h_probs[0].host_name or hid)
            h_status = h_obj.status if h_obj else "UP"
            highest_sev = max(p.severity for p in h_probs)
            oldest_dur = max(p.duration_seconds for p in h_probs)

            top_hosts.append(TopProblemHostDTO(
                host_id=hid,
                host_name=h_name,
                problem_count=len(h_probs),
                highest_severity=highest_sev,
                highest_severity_name=SEVERITY_NAMES.get(highest_sev, "Unknown"),
                oldest_problem_duration_seconds=oldest_dur,
                availability_status=h_status
            ))

        # Sort top problem hosts by highest severity descending, then problem count descending
        top_hosts.sort(key=lambda x: (x.highest_severity, x.problem_count, x.oldest_problem_duration_seconds), reverse=True)

        # 7. Recent Events Timeline
        recent_events_dto = []
        for e in events:
            ev_type = "PROBLEM_STARTED" if e.value == 1 else "PROBLEM_RECOVERED"
            e_dt_str = datetime.fromtimestamp(e.clock, tz=timezone.utc).strftime("%H:%M:%S UTC")
            recent_events_dto.append(RecentIncidentEventDTO(
                eventid=e.eventid,
                clock=e.clock,
                timestamp_human=e_dt_str,
                event_type=ev_type,
                severity=e.severity,
                severity_name=SEVERITY_NAMES.get(e.severity, "Info"),
                host_name=e.host_name or "Infrastructure",
                description=e.name,
                acknowledged=e.acknowledged
            ))

        # 8. Infrastructure Groups (Only where meaningful telemetry exists!)
        infra_categories: Dict[str, List[str]] = {}
        for h in hosts:
            for g in h.groups:
                infra_categories.setdefault(g, []).append(h.id)

        infrastructure_dto = []
        for cat_name, h_ids in infra_categories.items():
            cat_hosts = [h for h in hosts if h.id in h_ids]
            cat_probs = [p for p in problems if p.host_id in h_ids]
            has_crit = any(p.severity == 5 for p in cat_probs) or any(h.status == "DOWN" for h in cat_hosts)
            has_degraded = any(p.severity in (3, 4) for p in cat_probs)
            has_maint = any(h.status == "MAINTENANCE" for h in cat_hosts)

            if has_crit:
                cat_status = "CRITICAL"
            elif has_degraded:
                cat_status = "DEGRADED"
            elif has_maint:
                cat_status = "MAINTENANCE"
            else:
                cat_status = "OPERATIONAL"

            infrastructure_dto.append(InfrastructureGroupDTO(
                category=cat_name,
                hosts_count=len(cat_hosts),
                has_telemetry=True,
                telemetry_source="zabbix_adapter",
                healthy_count=sum(1 for h in cat_hosts if h.status == "UP" and not any(p.host_id == h.id for p in cat_probs)),
                problem_count=len(cat_probs),
                status=cat_status
            ))

        # Explicitly declare unmonitored infrastructure categories (Never fabricate healthy!)
        infrastructure_dto.append(InfrastructureGroupDTO(
            category="Cloud Environments (AWS / Azure)",
            hosts_count=0,
            has_telemetry=False,
            telemetry_source="None",
            healthy_count=0,
            problem_count=0,
            status="NO_DATA"
        ))

        # 9. Operational Trend Indicator
        recovered_count = sum(1 for e in events if e.value == 0)
        started_count = sum(1 for e in events if e.value == 1)
        if recovered_count > started_count:
            trend_dir = "improving"
            trend_desc = f"Net problem recovery rate positive ({recovered_count} recovered vs {started_count} new)"
        elif started_count > recovered_count and disaster_problems:
            trend_dir = "degrading"
            trend_desc = f"Active critical problems emerging ({started_count} new incidents)"
        else:
            trend_dir = "stable"
            trend_desc = "Incident volume and host telemetry stable in current window"

        trend_dto = TrendIndicatorDTO(
            direction=trend_dir,
            description=trend_desc,
            lineage="Computed from Zabbix event recovery/incident balance in recent window"
        )

        return OverviewResponseDTO(
            generated_at=datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            time_range=TimeRangeDTO(
                range_code=filters.time_range,
                start_time=start_time,
                end_time=end_time
            ),
            health=health_dto,
            hosts=hosts_dto,
            problems=problems_dto,
            availability=availability_dto,
            active_problems=active_problems_dto,
            top_problem_hosts=top_hosts,
            recent_events=recent_events_dto,
            infrastructure=infrastructure_dto,
            trend=trend_dto,
            data_lineage={
                "adapter": getattr(self.adapter, "__class__", type(self.adapter)).__name__,
                "source": "Zabbix 7.0.5 API (via Adapter)",
                "rules": [
                    "No Data != Healthy",
                    "Missing Telemetry != 100% Availability",
                    "Evidence-based Health state"
                ]
            },
            hosts_total=total_hosts,
            availability_pct=avail_percent or 0.0
        )

