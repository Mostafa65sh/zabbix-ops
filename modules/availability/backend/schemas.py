from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LinkedProblemDTO(BaseModel):
    eventid: str
    severity: int
    severity_name: str
    name: str
    clock: int


class ExcludedDowntimeDTO(BaseModel):
    name: str
    period_from: int
    period_to: int
    duration_seconds: int


class AvailabilityOverviewDTO(BaseModel):
    overall_status: str                     # "OK" | "DEGRADED" | "CRITICAL" | "NO_DATA"
    average_sli: Optional[float] = None    # None if NO_DATA
    average_sli_formatted: str             # "99.85%" | "NO_DATA"
    sla_compliance_rate: Optional[float] = None   # Percentage of compliant SLAs
    service_compliance_rate: Optional[float] = None # Percentage of compliant services
    total_services: int
    services_ok: int
    services_problem: int
    services_no_data: int
    services_compliant: int = 0             # Number of compliant services
    services_breached: int = 0              # Number of breached services
    total_slas: int
    slas_compliant: int
    slas_breached: int
    total_downtime_seconds: int
    total_excluded_downtime_seconds: int
    measured_period: str                   # e.g., "Last 30 Days"
    data_lineage: Dict[str, Any]
    generated_at: str


class ServiceAvailabilityItemDTO(BaseModel):
    service_id: str
    name: str
    status: str                            # "OK" | "WARNING" | "AVERAGE" | "HIGH" | "DISASTER"
    status_int: int                        # 0 to 5
    sla_id: Optional[str] = None
    sla_name: Optional[str] = None
    slo_target: Optional[float] = None
    sli_current: Optional[float] = None    # None if NO_DATA / sli == -1.0
    sli_formatted: str                     # e.g. "99.95%" | "NO_DATA"
    sla_status: str                        # "COMPLIANT" | "BREACHED" | "NO_DATA" | "NOT_CONFIGURED"
    uptime_seconds: int
    downtime_seconds: int
    error_budget_seconds: Optional[int] = None
    error_budget_formatted: str            # "+2h 15m" | "-45m" | "NO_DATA"
    problem_count: int
    problem_events: List[LinkedProblemDTO] = Field(default_factory=list)
    tags: List[Dict[str, str]] = Field(default_factory=list)
    slas: List[Dict[str, Any]] = Field(default_factory=list)  # Preserves all authoritative SLA memberships with telemetry


class ServiceAvailabilityListDTO(BaseModel):
    items: List[ServiceAvailabilityItemDTO]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    summary: Dict[str, Any]


class SLADefinitionItemDTO(BaseModel):
    sla_id: str
    name: str
    period: str                            # "daily" | "weekly" | "monthly" | "quarterly" | "annually"
    slo_target: float
    timezone: str
    status: str                            # "ENABLED" | "DISABLED"
    service_count: int
    current_sli: Optional[float] = None
    sli_formatted: str
    compliance_status: str                 # "COMPLIANT" | "BREACHED" | "NO_DATA"
    error_budget_seconds: Optional[int] = None
    error_budget_human: str
    excluded_downtimes: List[ExcludedDowntimeDTO] = Field(default_factory=list)


class SLAListResponseDTO(BaseModel):
    items: List[SLADefinitionItemDTO]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class AvailabilityTrendPointDTO(BaseModel):
    period_from: int
    period_to: int
    period_label: str                      # e.g., "2026-09" or "Period 1"
    sli_percent: Optional[float] = None    # None if NO_DATA
    sli_formatted: str
    uptime_seconds: int
    downtime_seconds: int
    error_budget_seconds: Optional[int] = None
    excluded_downtime_seconds: int
    is_compliant: Optional[bool] = None


class AvailabilityTrendResponseDTO(BaseModel):
    sla_id: str
    sla_name: str
    slo_target: float
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    period_type: str
    points: List[AvailabilityTrendPointDTO]
    generated_at: str


class ModuleStatusDTO(BaseModel):
    module: str
    name: str
    status: str
    version: str
    declared_permission: str
