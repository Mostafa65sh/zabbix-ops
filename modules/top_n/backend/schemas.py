from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TopNStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
    declared_permission: str


class TopNMetricValueDTO(BaseModel):
    value: Optional[float] = None
    formatted: str = "NO_DATA"
    status: str = "NO_DATA"  # "NORMAL", "WARNING", "CRITICAL", "NO_DATA"
    unit: str = "%"


class TopNItemDTO(BaseModel):
    rank: int
    host_id: str
    host_name: str
    technical_name: str
    primary_ip: str = ""
    status: str  # "UP", "DOWN", "MAINTENANCE"
    availability: str  # "AVAILABLE", "UNAVAILABLE", "UNKNOWN"
    groups: List[str] = Field(default_factory=list)
    metric_name: str  # "cpu", "memory", "storage", "problems"
    metric_value: TopNMetricValueDTO
    raw_value: Optional[float] = None
    active_problems_count: int = 0
    highest_severity: Optional[int] = None
    tags: List[Dict[str, str]] = Field(default_factory=list)


class TopNResponseDTO(BaseModel):
    metric: str
    metric_display_name: str
    order: str  # "desc", "asc"
    items: List[TopNItemDTO]
    total_evaluated_hosts: int
    is_truncated: bool = False
    truncation_reason: Optional[str] = None
    generated_at: str


class TopNOverviewResponseDTO(BaseModel):
    cpu: List[TopNItemDTO]
    memory: List[TopNItemDTO]
    storage: List[TopNItemDTO]
    problems: List[TopNItemDTO]
    total_evaluated_hosts: int
    is_truncated: bool = False
    truncation_reason: Optional[str] = None
    generated_at: str
