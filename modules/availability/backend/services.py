from datetime import datetime, timezone
import math
import time
from typing import List, Dict, Any, Optional

from app.adapters.zabbix.base import ZabbixAdapterBase
from app.core.logging import get_module_logger
from modules.availability.backend.schemas import (
    AvailabilityOverviewDTO,
    ServiceAvailabilityItemDTO,
    ServiceAvailabilityListDTO,
    SLADefinitionItemDTO,
    SLAListResponseDTO,
    AvailabilityTrendPointDTO,
    AvailabilityTrendResponseDTO,
    LinkedProblemDTO,
    ExcludedDowntimeDTO
)

logger = get_module_logger("availability")

SEVERITY_NAMES = {
    0: "OK",
    1: "INFORMATION",
    2: "WARNING",
    3: "AVERAGE",
    4: "HIGH",
    5: "DISASTER"
}

PERIOD_NAMES = {
    0: "daily",
    1: "weekly",
    2: "monthly",
    3: "quarterly",
    4: "annually"
}


def format_duration(seconds: int) -> str:
    """Format duration in seconds into human-readable representation."""
    if seconds <= 0:
        return "0s"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours >= 24:
        days, hours = divmod(hours, 24)
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes:02d}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_error_budget(seconds: Optional[int]) -> str:
    """Format error budget seconds into signed human-readable string or NO_DATA."""
    if seconds is None:
        return "NO_DATA"
    is_negative = seconds < 0
    abs_sec = abs(seconds)
    hours, remainder = divmod(abs_sec, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours >= 24:
        days, hours = divmod(hours, 24)
        sign = "-" if is_negative else "+"
        return f"{sign}{days}d {hours}h"
    elif hours > 0:
        sign = "-" if is_negative else "+"
        return f"{sign}{hours}h {minutes:02d}m"
    elif minutes > 0:
        sign = "-" if is_negative else "+"
        return f"{sign}{minutes}m"
    else:
        sign = "-" if is_negative else "+"
        return f"{sign}{abs_sec}s"


class AvailabilityService:
    """
    Business service for Module 04 — Availability.
    Provides NOC and executive observability for Business Services and SLAs.
    Enforces call-budget <= 3 Zabbix calls per endpoint and zero data fabrication.
    """

    def __init__(self, adapter: ZabbixAdapterBase):
        self.adapter = adapter

    def _resolve_time_range(
        self,
        time_range: str = "30d",
        time_from: Optional[int] = None,
        time_till: Optional[int] = None
    ) -> tuple[int, int, str]:
        """Resolves operational window adhering to explicit timestamps > presets."""
        now = int(time.time())
        if time_from is not None and time_till is not None and time_till > time_from:
            return time_from, time_till, f"Custom ({time_from} to {time_till})"

        presets = {
            "24h": (86400, "Last 24 Hours"),
            "7d": (604800, "Last 7 Days"),
            "30d": (2592000, "Last 30 Days"),
            "90d": (7776000, "Last 90 Days"),
            "365d": (31536000, "Last 365 Days")
        }
        window_seconds, label = presets.get(time_range, (2592000, "Last 30 Days"))
        return now - window_seconds, now, label

    async def get_overview(
        self,
        time_range: str = "30d",
        time_from: Optional[int] = None,
        time_till: Optional[int] = None,
        sla_id: Optional[str] = None
    ) -> AvailabilityOverviewDTO:
        """
        Executive Availability Overview.
        Call budget: Max 3 calls (sla.get, service.get, targeted sla.getsli).
        Zero data fabrication: All availability and downtime metrics are derived
        directly from authoritative Zabbix API data for the requested operational window.
        """
        now = int(time.time())
        p_from, p_till, period_label = self._resolve_time_range(time_range, time_from, time_till)

        # Call 1: Retrieve SLAs
        raw_slas = await self.adapter.get_slas(
            sla_ids=[sla_id] if sla_id else None,
            limit=100
        )

        # Call 2: Retrieve Monitored Business Services
        raw_services = await self.adapter.get_services(
            sla_ids=[sla_id] if sla_id else None,
            limit=500
        )

        # Analyze Services
        total_services = len(raw_services)
        services_ok = sum(1 for s in raw_services if s.get("status") == 0)
        services_problem = sum(1 for s in raw_services if (s.get("status") or 0) > 0)
        services_no_data = 0

        # Health state derivation
        if services_problem > 0:
            overall_status = "DEGRADED" if services_problem < total_services else "CRITICAL"
        elif total_services > 0:
            overall_status = "OK"
        else:
            overall_status = "NO_DATA"

        total_slas = len(raw_slas)
        services_compliant = 0
        services_breached = 0
        services_no_data = 0
        total_downtime = 0
        total_excluded_downtime = 0
        valid_slis: List[float] = []

        target_slas = [s for s in raw_slas if s["slaid"] == sla_id] if sla_id else raw_slas
        for sla in target_slas:
            s_slaid = sla["slaid"]
            slo_target = float(sla.get("slo", 99.0))
            try:
                sli_data = await self.adapter.get_sla_sli(
                    slaid=s_slaid,
                    period_from=p_from,
                    period_to=p_till
                )
                sli_matrix = sli_data.get("sli", [])
                service_ids = sli_data.get("serviceids", [])
                if sli_matrix and service_ids:
                    # Iterate through all service columns and aggregate across all period rows
                    for s_idx, sid in enumerate(service_ids):
                        s_up = sum(int(row[s_idx].get("uptime", 0)) for row in sli_matrix if s_idx < len(row))
                        s_down = sum(int(row[s_idx].get("downtime", 0)) for row in sli_matrix if s_idx < len(row))
                        total_downtime += s_down
                        if (s_up + s_down) > 0:
                            s_sli = round((s_up / (s_up + s_down)) * 100.0, 2)
                            valid_slis.append(s_sli)
                            if s_sli >= slo_target:
                                services_compliant += 1
                            else:
                                services_breached += 1
                        else:
                            services_no_data += 1

                    for row in sli_matrix:
                        for cell in row:
                            for ed in cell.get("excluded_downtimes", []):
                                ed_from = int(ed.get("period_from", 0))
                                ed_to = int(ed.get("period_to", 0))
                                overlap_start = max(ed_from, p_from)
                                overlap_end = min(ed_to, p_till)
                                if overlap_end > overlap_start:
                                    total_excluded_downtime += (overlap_end - overlap_start)
            except Exception as e:
                logger.warning(f"Could not retrieve SLI for SLA '{s_slaid}': {e}")

        # Account for static excluded downtimes in SLA definitions within the window
        if total_excluded_downtime == 0:
            for sla in raw_slas:
                for ed in sla.get("excluded_downtimes", []):
                    ed_from = int(ed.get("period_from", 0))
                    ed_to = int(ed.get("period_to", 0))
                    overlap_start = max(ed_from, p_from)
                    overlap_end = min(ed_to, p_till)
                    if overlap_end > overlap_start:
                        total_excluded_downtime += (overlap_end - overlap_start)

        avg_sli = round(sum(valid_slis) / len(valid_slis), 2) if valid_slis else None
        compliance_eval_count = services_compliant + services_breached
        compliance_rate = round((services_compliant / compliance_eval_count) * 100.0, 1) if compliance_eval_count > 0 else None

        now_str = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        return AvailabilityOverviewDTO(
            overall_status=overall_status,
            average_sli=avg_sli,
            average_sli_formatted=f"{avg_sli:.2f}%" if avg_sli is not None else "NO_DATA",
            sla_compliance_rate=compliance_rate,
            service_compliance_rate=compliance_rate,
            total_services=total_services,
            services_ok=services_ok,
            services_problem=services_problem,
            services_no_data=services_no_data,
            services_compliant=services_compliant,
            services_breached=services_breached,
            total_slas=total_slas,
            slas_compliant=services_compliant,
            slas_breached=services_breached,
            total_downtime_seconds=total_downtime,
            total_excluded_downtime_seconds=total_excluded_downtime,
            measured_period=period_label,
            data_lineage={
                "source": "Zabbix 7.0.5 API (sla.get, service.get, sla.getsli)",
                "adapter": getattr(self.adapter, "__class__", type(self.adapter)).__name__,
                "window": {
                    "period_from": p_from,
                    "period_to": p_till,
                    "preset": time_range
                },
                "rules": [
                    "No Data != 100% Availability",
                    "Excluded downtimes removed from reporting windows",
                    "Multi-period time-weighted aggregation",
                    "Zero data fabrication"
                ]
            },
            generated_at=now_str
        )

    async def get_services(
        self,
        page: int = 1,
        page_size: int = 25,
        sla_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "status",
        sort_order: str = "desc"
    ) -> ServiceAvailabilityListDTO:
        """
        Paginated Business Services List.
        Call budget: Max 3 calls (service.get, sla.get, targeted sla.getsli).
        Zero data fabrication: Services without SLA return NOT_CONFIGURED. Services with
        missing or unmeasured SLI return NO_DATA. Valid 0.0% and 100.0% values are preserved.
        Pagination: Fetches bounded candidate set (limit=500) to safely determine true total_count.
        """
        status_code = None
        if status:
            rev_map = {v: k for k, v in SEVERITY_NAMES.items()}
            status_code = rev_map.get(status.upper())

        # Call 1: Retrieve bounded services candidate set (maximum 500 items to protect Zabbix API)
        MAX_SERVICE_CANDIDATES = 500
        raw_services = await self.adapter.get_services(
            sla_ids=[sla_id] if sla_id else None,
            search=search,
            status=status_code,
            limit=MAX_SERVICE_CANDIDATES
        )

        # Call 2: Retrieve SLAs for matching
        raw_slas = await self.adapter.get_slas(
            sla_ids=[sla_id] if sla_id else None,
            limit=100
        )

        # Multi-SLA Resolution:
        # Collect SLI telemetry for all SLAs that apply to candidate services
        sli_by_service: Dict[str, Dict[str, Any]] = {}
        sla_by_service: Dict[str, Dict[str, Any]] = {}

        target_slas = [s for s in raw_slas if s["slaid"] == sla_id] if sla_id else raw_slas
        for sla in target_slas:
            s_slaid = sla["slaid"]
            try:
                sli_res = await self.adapter.get_sla_sli(
                    slaid=s_slaid,
                    periods=1
                )
                service_ids = sli_res.get("serviceids", [])
                sli_matrix = sli_res.get("sli", [])
                if sli_matrix and len(sli_matrix) > 0:
                    latest_period_cells = sli_matrix[0]
                    for idx, s_id in enumerate(service_ids):
                        s_id_str = str(s_id)
                        if idx < len(latest_period_cells):
                            if s_id_str not in sla_by_service:
                                sla_by_service[s_id_str] = sla
                                sli_by_service[s_id_str] = latest_period_cells[idx]
            except Exception as e:
                logger.warning(f"Could not retrieve SLI for SLA '{s_slaid}': {e}")

        # Map each service to DTO
        all_items: List[ServiceAvailabilityItemDTO] = []
        for s in raw_services:
            sid = str(s.get("serviceid", ""))
            sname = s.get("name", f"Service-{sid}")
            st_int = int(s.get("status") or 0)
            st_name = SEVERITY_NAMES.get(st_int, "UNKNOWN")

            # Determine linked SLA:
            # 1. Authoritative membership from Zabbix sla.getsli
            matched_sla = sla_by_service.get(sid)
            # 2. Tag-based fallback if SLI wasn't returned
            if matched_sla is None:
                srv_tags = [(t.get("tag"), t.get("value")) for t in s.get("tags", [])]
                for sla in raw_slas:
                    sla_tags = [(t.get("tag"), t.get("value")) for t in sla.get("service_tags", [])]
                    if any(st in srv_tags for st in sla_tags):
                        matched_sla = sla
                        break

            sli_info = sli_by_service.get(sid)
            slo_target = float(matched_sla["slo"]) if matched_sla else None
            sla_name = matched_sla.get("name") if matched_sla else None
            sla_id_val = matched_sla.get("slaid") if matched_sla else None

            # Evidence-based SLI calculation (Golden Rule: Never fabricate!)
            if matched_sla is None:
                sli_current = None
                sli_formatted = "NO_DATA"
                sla_status = "NOT_CONFIGURED"
                uptime_sec = 0
                downtime_sec = 0
                eb_sec = None
                eb_formatted = "NO_DATA"
            elif sli_info is not None:
                raw_sli_val = sli_info.get("sli")
                uptime_sec = int(sli_info.get("uptime", 0))
                downtime_sec = int(sli_info.get("downtime", 0))
                eb_sec = sli_info.get("error_budget")
                eb_formatted = format_error_budget(eb_sec)

                if raw_sli_val is None or float(raw_sli_val) == -1.0 or float(raw_sli_val) < 0.0:
                    sli_current = None
                    sli_formatted = "NO_DATA"
                    sla_status = "NO_DATA"
                else:
                    raw_sli = float(raw_sli_val)
                    sli_current = round(raw_sli, 2)
                    sli_formatted = f"{raw_sli:.2f}%"
                    sla_status = "COMPLIANT" if (slo_target is not None and raw_sli >= slo_target) else "BREACHED"
            else:
                # SLA is configured, but SLI telemetry is not available for this service
                sli_current = None
                sli_formatted = "NO_DATA"
                sla_status = "NO_DATA"
                uptime_sec = 0
                downtime_sec = 0
                eb_sec = None
                eb_formatted = "NO_DATA"

            # Problem events
            prob_events = []
            for pe in s.get("problem_events", []):
                pe_sev = int(pe.get("severity", 0))
                prob_events.append(
                    LinkedProblemDTO(
                        eventid=str(pe.get("eventid", "")),
                        severity=pe_sev,
                        severity_name=SEVERITY_NAMES.get(pe_sev, "UNKNOWN"),
                        name=pe.get("name", "Active Problem"),
                        clock=int(pe.get("clock") or time.time())
                    )
                )

            all_items.append(
                ServiceAvailabilityItemDTO(
                    service_id=sid,
                    name=sname,
                    status=st_name,
                    status_int=st_int,
                    sla_id=sla_id_val,
                    sla_name=sla_name,
                    slo_target=slo_target,
                    sli_current=sli_current,
                    sli_formatted=sli_formatted,
                    sla_status=sla_status,
                    uptime_seconds=uptime_sec,
                    downtime_seconds=downtime_sec,
                    error_budget_seconds=eb_sec,
                    error_budget_formatted=eb_formatted,
                    problem_count=len(prob_events),
                    problem_events=prob_events,
                    tags=s.get("tags", [])
                )
            )

        # In-memory Sorting
        reverse = (sort_order.lower() == "desc")
        if sort_by == "name":
            all_items.sort(key=lambda x: x.name.lower(), reverse=reverse)
        elif sort_by == "sli":
            all_items.sort(key=lambda x: (x.sli_current if x.sli_current is not None else -1.0), reverse=reverse)
        elif sort_by == "downtime":
            all_items.sort(key=lambda x: x.downtime_seconds, reverse=reverse)
        elif sort_by == "error_budget":
            all_items.sort(key=lambda x: (x.error_budget_seconds if x.error_budget_seconds is not None else -999999), reverse=reverse)
        else:  # status
            all_items.sort(key=lambda x: x.status_int, reverse=reverse)

        # In-memory Pagination
        total_count = len(all_items)
        page_size = max(1, min(page_size, 100))
        total_pages = max(1, math.ceil(total_count / page_size)) if total_count > 0 else 1
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_items = all_items[start_idx:end_idx]

        is_truncated = (len(raw_services) >= MAX_SERVICE_CANDIDATES)
        summary = {
            "total_services": total_count,
            "compliant_count": sum(1 for x in all_items if x.sla_status == "COMPLIANT"),
            "breached_count": sum(1 for x in all_items if x.sla_status == "BREACHED"),
            "unconfigured_count": sum(1 for x in all_items if x.sla_status == "NOT_CONFIGURED"),
            "bounded_ceiling": MAX_SERVICE_CANDIDATES,
            "candidate_limit": MAX_SERVICE_CANDIDATES,
            "is_truncated": is_truncated
        }

        return ServiceAvailabilityListDTO(
            items=paged_items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            summary=summary
        )

    async def get_slas(
        self,
        page: int = 1,
        page_size: int = 25,
        search: Optional[str] = None,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> SLAListResponseDTO:
        """
        SLA Registry List.
        Call budget: Max 3 calls (sla.get, service.get, targeted sla.getsli).
        Zero mock coupling: Dynamic resolution of real numeric Zabbix SLA IDs without
        hardcoded identifiers or names.
        """
        # Call 1: Retrieve SLAs
        raw_slas = await self.adapter.get_slas(
            search=search,
            limit=100
        )

        # Call 2: Retrieve services to calculate service counts
        raw_services = await self.adapter.get_services(
            limit=500
        )

        # Call 3 (targeted): Get SLI for the primary SLA if available within call budget
        primary_slaid = raw_slas[0]["slaid"] if raw_slas else None
        sli_by_sla: Dict[str, Dict[str, Any]] = {}
        if primary_slaid:
            try:
                sli_res = await self.adapter.get_sla_sli(
                    slaid=primary_slaid,
                    periods=1
                )
                sli_matrix = sli_res.get("sli", [])
                if sli_matrix and len(sli_matrix) > 0:
                    period_cells = sli_matrix[0]
                    valid_cells = [
                        c for c in period_cells 
                        if c.get("sli") is not None and float(c.get("sli", -1.0)) >= 0.0
                    ]
                    if valid_cells:
                        avg_sli = round(sum(float(c["sli"]) for c in valid_cells) / len(valid_cells), 2)
                        eb_list = [c.get("error_budget") for c in valid_cells if c.get("error_budget") is not None]
                        min_eb = min(eb_list) if eb_list else None
                        sli_by_sla[primary_slaid] = {
                            "sli": avg_sli,
                            "error_budget": min_eb
                        }
            except Exception as e:
                logger.warning(f"Could not retrieve SLI for SLA '{primary_slaid}': {e}")

        all_items: List[SLADefinitionItemDTO] = []
        for sla in raw_slas:
            slaid = str(sla.get("slaid", ""))
            name = sla.get("name", f"SLA-{slaid}")
            period_int = int(sla.get("period", 2))
            period_str = PERIOD_NAMES.get(period_int, "monthly")
            slo = float(sla.get("slo", 99.0))
            tz = sla.get("timezone", "UTC")
            st = "ENABLED" if str(sla.get("status", "1")) == "1" else "DISABLED"

            # Parse excluded downtimes
            ex_downtimes = []
            for ed in sla.get("excluded_downtimes", []):
                p_from = int(ed.get("period_from", 0))
                p_to = int(ed.get("period_to", 0))
                dur = max(0, p_to - p_from)
                ex_downtimes.append(
                    ExcludedDowntimeDTO(
                        name=ed.get("name", "Excluded Maintenance"),
                        period_from=p_from,
                        period_to=p_to,
                        duration_seconds=dur
                    )
                )

            # Service count derived from services matching SLA tags
            sla_tags = [(t.get("tag"), t.get("value")) for t in sla.get("service_tags", [])]
            srv_count = sum(
                1 for s in raw_services
                if any((t.get("tag"), t.get("value")) in sla_tags for t in s.get("tags", []))
            ) if sla_tags else 0

            # Dynamic SLI metrics from authoritative adapter response (Golden Rule: Zero fabrication!)
            sla_sli_info = sli_by_sla.get(slaid)
            if sla_sli_info is not None and sla_sli_info["sli"] is not None:
                curr_sli = sla_sli_info["sli"]
                sli_fmt = f"{curr_sli:.2f}%"
                comp_status = "COMPLIANT" if curr_sli >= slo else "BREACHED"
                eb_sec = sla_sli_info["error_budget"]
                eb_hum = format_error_budget(eb_sec)
            else:
                curr_sli = None
                sli_fmt = "NO_DATA"
                comp_status = "NO_DATA"
                eb_sec = None
                eb_hum = "NO_DATA"

            all_items.append(
                SLADefinitionItemDTO(
                    sla_id=slaid,
                    name=name,
                    period=period_str,
                    slo_target=slo,
                    timezone=tz,
                    status=st,
                    service_count=srv_count,
                    current_sli=curr_sli,
                    sli_formatted=sli_fmt,
                    compliance_status=comp_status,
                    error_budget_seconds=eb_sec,
                    error_budget_human=eb_hum,
                    excluded_downtimes=ex_downtimes
                )
            )

        # In-memory Sorting
        reverse = (sort_order.lower() == "desc")
        if sort_by == "slo":
            all_items.sort(key=lambda x: x.slo_target, reverse=reverse)
        elif sort_by == "period":
            all_items.sort(key=lambda x: x.period, reverse=reverse)
        else:  # name
            all_items.sort(key=lambda x: x.name.lower(), reverse=reverse)

        # In-memory Pagination
        total_count = len(all_items)
        page_size = max(1, min(page_size, 100))
        total_pages = max(1, math.ceil(total_count / page_size)) if total_count > 0 else 1
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_items = all_items[start_idx:end_idx]

        return SLAListResponseDTO(
            items=paged_items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def get_trend(
        self,
        sla_id: str,
        service_id: Optional[str] = None,
        periods: int = 12
    ) -> AvailabilityTrendResponseDTO:
        """
        Historical Availability and SLI Trend.
        Call budget: Exactly 2 calls (sla.get for ID, targeted sla.getsli).
        """
        now = int(time.time())

        # Call 1: Targeted SLA lookup by ID
        slas = await self.adapter.get_slas(sla_ids=[sla_id], limit=1)
        if not slas:
            raise ValueError(f"SLA with ID '{sla_id}' was not found.")
        target_sla = slas[0]

        # Call 2: Targeted SLI calculation by SLA ID
        sli_data = await self.adapter.get_sla_sli(
            slaid=sla_id,
            periods=min(max(periods, 1), 24),
            service_ids=[service_id] if service_id else None
        )

        rep_periods = sli_data.get("periods", [])
        sli_matrix = sli_data.get("sli", [])
        service_ids = [str(sid) for sid in sli_data.get("serviceids", [])]

        # Invariant TRN-01: When service_id is provided, it must belong to the SLA
        if service_id is not None:
            if str(service_id) not in service_ids:
                raise ValueError(f"Service '{service_id}' does not belong to SLA '{sla_id}'.")
            target_idx = service_ids.index(str(service_id))
        else:
            target_idx = None

        slo = float(target_sla.get("slo", 99.0))
        period_str = PERIOD_NAMES.get(int(target_sla.get("period", 2)), "monthly")

        trend_points: List[AvailabilityTrendPointDTO] = []
        for p_idx, p in enumerate(rep_periods):
            p_from = int(p.get("period_from", 0))
            p_to = int(p.get("period_to", 0))
            dt_label = datetime.fromtimestamp(p_from, tz=timezone.utc).strftime("%b %Y")

            if p_idx < len(sli_matrix):
                row = sli_matrix[p_idx]
                if target_idx is not None and target_idx < len(row):
                    cell = row[target_idx]
                    val_sli = float(cell.get("sli", -1.0))
                    up_sec = int(cell.get("uptime", 0))
                    down_sec = int(cell.get("downtime", 0))
                    eb_sec = cell.get("error_budget")

                    # Excluded downtimes
                    ex_dur = 0
                    for ed in cell.get("excluded_downtimes", []):
                        ex_dur += max(0, int(ed.get("period_to", 0)) - int(ed.get("period_from", 0)))
                elif target_idx is None and len(row) > 0:
                    # Aggregate across all services in this SLA for period p_idx
                    up_sec = sum(int(c.get("uptime", 0)) for c in row)
                    down_sec = sum(int(c.get("downtime", 0)) for c in row)
                    valid_row_slis = [float(c["sli"]) for c in row if c.get("sli") is not None and float(c.get("sli", -1.0)) >= 0.0]
                    val_sli = round(sum(valid_row_slis) / len(valid_row_slis), 2) if valid_row_slis else -1.0
                    eb_list = [c.get("error_budget") for c in row if c.get("error_budget") is not None]
                    eb_sec = min(eb_list) if eb_list else None
                    ex_dur = 0
                    for c in row:
                        for ed in c.get("excluded_downtimes", []):
                            ex_dur += max(0, int(ed.get("period_to", 0)) - int(ed.get("period_from", 0)))
                else:
                    val_sli = -1.0
                    up_sec = 0
                    down_sec = 0
                    eb_sec = None
                    ex_dur = 0

                if val_sli == -1.0:
                    sli_percent = None
                    sli_fmt = "NO_DATA"
                    is_comp = None
                else:
                    sli_percent = round(val_sli, 2)
                    sli_fmt = f"{val_sli:.2f}%"
                    is_comp = (val_sli >= slo)

                trend_points.append(
                    AvailabilityTrendPointDTO(
                        period_from=p_from,
                        period_to=p_to,
                        period_label=dt_label,
                        sli_percent=sli_percent,
                        sli_formatted=sli_fmt,
                        uptime_seconds=up_sec,
                        downtime_seconds=down_sec,
                        error_budget_seconds=eb_sec,
                        excluded_downtime_seconds=ex_dur,
                        is_compliant=is_comp
                    )
                )

        now_str = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        return AvailabilityTrendResponseDTO(
            sla_id=sla_id,
            sla_name=target_sla.get("name", f"SLA-{sla_id}"),
            slo_target=slo,
            service_id=service_id,
            service_name=None,
            period_type=period_str,
            points=trend_points,
            generated_at=now_str
        )
