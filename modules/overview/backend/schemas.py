from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TimeRangeDTO(BaseModel):
    range_code: str = Field(default="24h")
    start_time: int
    end_time: int


class HealthSummaryDTO(BaseModel):
    status: str = Field(description="HEALTHY, DEGRADED, CRITICAL, or UNKNOWN")
    reason: str = Field(description="Evidence-based key explaining status")
    evidence: List[str] = Field(default_factory=list)


class HostStatusSummaryDTO(BaseModel):
    total: int
    available: int
    unavailable: int
    unknown: int
    maintenance: int


class ProblemSeveritySummaryDTO(BaseModel):
    total: int
    disaster: int
    high: int
    average: int
    warning: int
    information: int


class AvailabilitySummaryDTO(BaseModel):
    percent: Optional[float] = Field(default=None, description="Measured percentage or None if no data")
    planned_downtime_seconds: int = 0
    unplanned_downtime_seconds: int = 0
    unknown_seconds: int = 0
    lineage: Dict[str, Any] = Field(default_factory=dict)


class ActiveProblemDTO(BaseModel):
    eventid: str
    severity: int
    severity_name: str
    name: str
    host_id: Optional[str] = None
    host_name: Optional[str] = None
    duration_seconds: int
    duration_human: str
    acknowledged: bool
    started_clock: int
    started_human: str


class TopProblemHostDTO(BaseModel):
    host_id: str
    host_name: str
    problem_count: int
    highest_severity: int
    highest_severity_name: str
    oldest_problem_duration_seconds: int
    availability_status: str


class RecentIncidentEventDTO(BaseModel):
    eventid: str
    clock: int
    timestamp_human: str
    event_type: str
    severity: int
    severity_name: str
    host_name: str
    description: str
    acknowledged: bool


class InfrastructureGroupDTO(BaseModel):
    category: str
    hosts_count: int
    has_telemetry: bool = True
    telemetry_source: str = "zabbix_adapter"
    healthy_count: int
    problem_count: int
    status: str  # "OPERATIONAL", "DEGRADED", "CRITICAL", "MAINTENANCE", "NO_DATA"


class TrendIndicatorDTO(BaseModel):
    direction: str = Field(description="improving, stable, degrading, or unknown")
    description: str
    lineage: str


class OverviewFilterParams(BaseModel):
    time_range: str = "24h"
    group: Optional[str] = None
    severity: Optional[int] = None
    status: Optional[str] = None
    host: Optional[str] = None


class OverviewResponseDTO(BaseModel):
    generated_at: str
    time_range: TimeRangeDTO
    health: HealthSummaryDTO
    hosts: HostStatusSummaryDTO
    problems: ProblemSeveritySummaryDTO
    availability: AvailabilitySummaryDTO
    active_problems: List[ActiveProblemDTO]
    top_problem_hosts: List[TopProblemHostDTO]
    recent_events: List[RecentIncidentEventDTO]
    infrastructure: List[InfrastructureGroupDTO]
    trend: TrendIndicatorDTO
    data_lineage: Dict[str, Any]

    # Backward compatibility aliases for Phase 0
    hosts_total: Optional[int] = None
    availability_pct: Optional[float] = None

