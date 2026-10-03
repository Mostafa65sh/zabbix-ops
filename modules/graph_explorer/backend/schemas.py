from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GraphExplorerStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
    declared_permission: str


class GraphPointDTO(BaseModel):
    clock: int
    timestamp_iso: str
    value: Optional[float] = None


class GraphMetricSeriesDTO(BaseModel):
    series_id: str  # e.g., "10001:cpu"
    host_id: str
    host_name: str
    metric_name: str  # "cpu", "memory", "storage"
    metric_label: str  # "CPU Utilization", etc.
    unit: str = "%"
    color: Optional[str] = None
    points: List[GraphPointDTO] = Field(default_factory=list)
    latest_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None


class MultiSeriesGraphResponseDTO(BaseModel):
    time_range: str
    time_from: int
    time_till: int
    series: List[GraphMetricSeriesDTO]
    total_series: int
    is_truncated: bool = False
    truncation_reason: Optional[str] = None
    generated_at: str


class GraphTargetDTO(BaseModel):
    host_id: str
    host_name: str
    technical_name: str
    primary_ip: str = ""
    status: str
    groups: List[str] = Field(default_factory=list)
    available_metrics: List[str] = Field(default_factory=list)


class GraphTargetsResponseDTO(BaseModel):
    targets: List[GraphTargetDTO]
    total_targets: int
    is_truncated: bool = False
    truncation_reason: Optional[str] = None
    generated_at: str
