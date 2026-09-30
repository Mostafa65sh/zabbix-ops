from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
import time

from app.adapters.zabbix.base import ZabbixAdapterBase
from modules.problems.backend.schemas import (
    ProblemItemDTO,
    ProblemHostDTO,
    ProblemTagDTO,
    ProblemAcknowledgeDTO,
    ProblemAlertDTO,
    ProblemDetailResponseDTO,
    ProblemSeveritySummaryDTO,
    ProblemListSummaryDTO,
    ProblemListResponseDTO,
    ProblemFilterParams
)

SEVERITY_MAP = {
    0: "UNCLASSIFIED",
    1: "INFORMATION",
    2: "WARNING",
    3: "AVERAGE",
    4: "HIGH",
    5: "DISASTER"
}


def format_duration(seconds: int) -> str:
    """Convert duration in seconds to human-readable string (e.g., 2d 4h, 15m 30s)."""
    if seconds < 0:
        return "0s"
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    rem_seconds = seconds % 60
    if minutes < 60:
        return f"{minutes}m {rem_seconds}s"
    hours = minutes // 60
    rem_minutes = minutes % 60
    if hours < 24:
        return f"{hours}h {rem_minutes}m"
    days = hours // 24
    rem_hours = hours % 24
    return f"{days}d {rem_hours}h"


def format_timestamp(ts: int) -> str:
    """Format Unix timestamp to human-readable UTC ISO-like format."""
    if not ts or ts <= 0:
        return "NO_DATA"
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return "NO_DATA"


class ProblemsService:
    def __init__(self, adapter: ZabbixAdapterBase):
        self.adapter = adapter

    def _map_raw_to_dto(self, raw: Dict[str, Any], now: Optional[int] = None) -> ProblemItemDTO:
        if now is None:
            now = int(time.time())

        clock = int(raw.get("clock") or 0)
        sev_int = int(raw.get("severity") or 0)
        sev_name = SEVERITY_MAP.get(sev_int, "UNCLASSIFIED")

        # Duration calculation from valid Zabbix clock
        r_clock = int(raw.get("r_clock") or 0)
        if r_clock > 0 and r_clock >= clock:
            dur_sec = r_clock - clock
        elif clock > 0:
            dur_sec = max(0, now - clock)
        else:
            dur_sec = 0
        dur_human = format_duration(dur_sec) if clock > 0 else "NO_DATA"

        is_ack = raw.get("acknowledged") == "1" or raw.get("acknowledged") is True
        is_supp = raw.get("suppressed") == "1" or raw.get("suppressed") is True

        # Golden rule: missing or empty opdata must be "NO_DATA"
        opdata = str(raw.get("opdata") or "").strip()
        if not opdata:
            opdata = "NO_DATA"

        # Cause / Symptom logic
        cause_id = raw.get("cause_eventid")
        if cause_id in (None, "0", 0, ""):
            is_cause = True
            is_symptom = False
            cause_eventid_val = None
        else:
            is_cause = False
            is_symptom = True
            cause_eventid_val = str(cause_id)

        # Hosts mapping
        hosts: List[ProblemHostDTO] = []
        for h in raw.get("hosts", []):
            hosts.append(
                ProblemHostDTO(
                    hostid=str(h.get("hostid") or ""),
                    host=str(h.get("host") or ""),
                    name=str(h.get("name") or h.get("host") or "")
                )
            )

        # Tags mapping
        tags: List[ProblemTagDTO] = []
        for t in raw.get("tags", []):
            tags.append(
                ProblemTagDTO(
                    tag=str(t.get("tag") or ""),
                    value=str(t.get("value") or "")
                )
            )

        # Acknowledges mapping
        acknowledges: List[ProblemAcknowledgeDTO] = []
        for a in raw.get("acknowledges", []):
            a_clock = int(a.get("clock") or 0)
            acknowledges.append(
                ProblemAcknowledgeDTO(
                    acknowledgeid=str(a.get("acknowledgeid") or ""),
                    userid=str(a.get("userid") or ""),
                    clock=a_clock,
                    time=format_timestamp(a_clock),
                    message=str(a.get("message") or ""),
                    action=str(a.get("action") or "0")
                )
            )

        # Sort acknowledges chronologically
        acknowledges.sort(key=lambda x: x.clock)

        return ProblemItemDTO(
            eventid=str(raw.get("eventid") or ""),
            severity=sev_int,
            severity_name=sev_name,
            name=str(raw.get("name") or "Unnamed Problem"),
            clock=clock,
            start_time=format_timestamp(clock),
            duration_seconds=dur_sec,
            duration_human=dur_human,
            acknowledged=is_ack,
            suppressed=is_supp,
            suppression_data=raw.get("suppression_data") or [],
            opdata=opdata,
            cause_eventid=cause_eventid_val,
            is_cause=is_cause,
            is_symptom=is_symptom,
            hosts=hosts,
            host_groups=[],
            tags=tags,
            acknowledges=acknowledges
        )

    def _calculate_mtta(self, raw_problems: List[Dict[str, Any]]) -> Tuple[Optional[float], str]:
        """
        Calculate MTTA (Mean Time to Acknowledge) for acknowledged incidents.
        For acknowledged incidents: first_ack_clock - problem_clock.
        Exclude unacknowledged incidents.
        If zero acknowledged incidents: mtta_seconds = null, mtta_human = "NO_DATA".
        Never return fabricated zero values.
        """
        ack_delays: List[int] = []
        for p in raw_problems:
            is_ack = p.get("acknowledged") == "1" or p.get("acknowledged") is True
            if not is_ack:
                continue

            prob_clock = int(p.get("clock") or 0)
            if prob_clock <= 0:
                continue

            acks = p.get("acknowledges") or []
            ack_clocks = [int(a.get("clock")) for a in acks if a.get("clock")]
            if ack_clocks:
                first_ack_clock = min(ack_clocks)
                delay = max(0, first_ack_clock - prob_clock)
                ack_delays.append(delay)

        if not ack_delays:
            return None, "NO_DATA"

        avg_seconds = sum(ack_delays) / len(ack_delays)
        return round(avg_seconds, 1), format_duration(int(avg_seconds))

    def _build_summary(
        self,
        raw_problems: List[Dict[str, Any]],
        now: Optional[int] = None
    ) -> ProblemListSummaryDTO:
        if now is None:
            now = int(time.time())

        sev_counts = {
            "disaster": 0,
            "high": 0,
            "average": 0,
            "warning": 0,
            "information": 0,
            "unclassified": 0
        }
        ack_count = 0
        unack_count = 0
        supp_count = 0

        for p in raw_problems:
            s = int(p.get("severity") or 0)
            if s == 5:
                sev_counts["disaster"] += 1
            elif s == 4:
                sev_counts["high"] += 1
            elif s == 3:
                sev_counts["average"] += 1
            elif s == 2:
                sev_counts["warning"] += 1
            elif s == 1:
                sev_counts["information"] += 1
            else:
                sev_counts["unclassified"] += 1

            if p.get("acknowledged") == "1" or p.get("acknowledged") is True:
                ack_count += 1
            else:
                unack_count += 1

            if p.get("suppressed") == "1" or p.get("suppressed") is True:
                supp_count += 1

        mtta_sec, mtta_hum = self._calculate_mtta(raw_problems)

        return ProblemListSummaryDTO(
            total_problems=len(raw_problems),
            by_severity=ProblemSeveritySummaryDTO(**sev_counts),
            acknowledged_count=ack_count,
            unacknowledged_count=unack_count,
            suppressed_count=supp_count,
            mtta_seconds=mtta_sec,
            mtta_human=mtta_hum,
            generated_at=datetime.fromtimestamp(now, tz=timezone.utc).isoformat()
        )

    async def get_problems(self, filters: ProblemFilterParams) -> ProblemListResponseDTO:
        now = int(time.time())

        # Determine native filter params
        # Stage 1: Get count using native countOutput
        # Native Zabbix supports severities, acknowledged, suppressed, time_from, time_till natively
        total_count = await self.adapter.get_problem_count(
            time_from=filters.time_from,
            time_till=filters.time_till,
            severities=filters.severities,
            acknowledged=filters.acknowledged,
            suppressed=filters.suppressed,
            search=filters.search
        )

        page_size = max(1, min(filters.page_size, 100))
        total_pages = max(1, (total_count + page_size - 1) // page_size) if total_count > 0 else 1
        page = max(1, min(filters.page, total_pages))
        offset = (page - 1) * page_size

        # Stage 2: Bounded retrieval
        # Retrieve bounded window
        raw_items = await self.adapter.get_problem_feed(
            time_from=filters.time_from,
            time_till=filters.time_till,
            severities=filters.severities,
            acknowledged=filters.acknowledged,
            suppressed=filters.suppressed,
            search=filters.search,
            sort_field=filters.sort,
            sort_order=filters.sortorder,
            limit=page_size,
            offset=offset
        )

        # Apply secondary host or group filtering if requested and not natively filtered
        filtered_items = raw_items
        if filters.host:
            h_low = filters.host.lower()
            filtered_items = [
                p for p in filtered_items
                if any(
                    h_low in h.get("name", "").lower() or h_low in h.get("host", "").lower()
                    for h in p.get("hosts", [])
                )
            ]
        if filters.group:
            g_low = filters.group.lower()
            filtered_items = [
                p for p in filtered_items
                if any(
                    g_low in t.get("value", "").lower()
                    for t in p.get("tags", [])
                    if t.get("tag", "").lower() in ("group", "hostgroup", "tier")
                )
            ]

        # Convert to DTOs
        dto_items = [self._map_raw_to_dto(raw, now=now) for raw in filtered_items]

        # Build summary over the operational set
        # For summary in list response, retrieve summary metrics
        summary = self._build_summary(raw_items, now=now)

        return ProblemListResponseDTO(
            items=dto_items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            summary=summary
        )

    async def get_summary(
        self,
        time_from: Optional[int] = None,
        time_till: Optional[int] = None,
        search: Optional[str] = None,
        group: Optional[str] = None,
        host: Optional[str] = None
    ) -> ProblemListSummaryDTO:
        now = int(time.time())
        # Summary retrieves active problems for calculation (1 bounded API call)
        raw_items = await self.adapter.get_problem_feed(
            time_from=time_from,
            time_till=time_till,
            search=search,
            limit=500,
            offset=0
        )

        if host:
            h_low = host.lower()
            raw_items = [
                p for p in raw_items
                if any(
                    h_low in h.get("name", "").lower() or h_low in h.get("host", "").lower()
                    for h in p.get("hosts", [])
                )
            ]

        return self._build_summary(raw_items, now=now)

    async def get_problem_detail(self, event_id: str) -> Optional[ProblemDetailResponseDTO]:
        now = int(time.time())
        raw_detail = await self.adapter.get_problem_detail(event_id)
        if not raw_detail:
            return None

        base_dto = self._map_raw_to_dto(raw_detail, now=now)

        alerts_dto: List[ProblemAlertDTO] = []
        for al in raw_detail.get("alerts", []):
            al_clock = int(al.get("clock") or 0)
            alerts_dto.append(
                ProblemAlertDTO(
                    alertid=str(al.get("alertid") or ""),
                    mediatypeid=str(al.get("mediatypeid") or ""),
                    clock=al_clock,
                    time=format_timestamp(al_clock),
                    sendto=str(al.get("sendto") or ""),
                    status=str(al.get("status") or ""),
                    error=str(al.get("error") or "")
                )
            )
        alerts_dto.sort(key=lambda x: x.clock)

        return ProblemDetailResponseDTO(
            **base_dto.model_dump(),
            alerts=alerts_dto
        )
