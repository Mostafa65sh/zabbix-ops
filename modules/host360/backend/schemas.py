from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Host360StatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
    declared_permission: str


class HostMetricValueDTO(BaseModel):
    value: Optional[float] = None
    formatted: str = "NO_DATA"
    status: str = "NO_DATA"  # "NORMAL", "WARNING", "CRITICAL", "NO_DATA"
    unit: str = "%"


class HostHardwareTelemetryDTO(BaseModel):
    cpu_utilization: HostMetricValueDTO = Field(default_factory=HostMetricValueDTO)
    cpu_cores: Optional[int] = None
    cpu_load_1m: Optional[float] = None
    cpu_load_5m: Optional[float] = None
    cpu_load_15m: Optional[float] = None
    memory_utilization: HostMetricValueDTO = Field(default_factory=HostMetricValueDTO)
    memory_total_bytes: Optional[int] = None
    memory_used_bytes: Optional[int] = None
    memory_free_bytes: Optional[int] = None
    storage_utilization: HostMetricValueDTO = Field(default_factory=HostMetricValueDTO)
    storage_total_bytes: Optional[int] = None
    storage_used_bytes: Optional[int] = None
    network_rx_rate: Optional[str] = None
    network_tx_rate: Optional[str] = None


class HostInterfaceDTO(BaseModel):
    interfaceid: str
    ip: str = ""
    dns: str = ""
    port: str = "10050"
    type: str = "AGENT"  # "AGENT", "SNMP", "IPMI", "JMX"
    is_main: bool = True
    availability: str = "UNKNOWN"  # "AVAILABLE", "UNAVAILABLE", "UNKNOWN"
    error: Optional[str] = None


class HostProblemEventDTO(BaseModel):
    eventid: str
    name: str
    severity: int
    severity_name: str
    clock: int
    acknowledged: bool = False
    opdata: Optional[str] = None


class Host360ListItemDTO(BaseModel):
    host_id: str
    name: str
    technical_name: str
    status: str  # "UP", "DOWN", "MAINTENANCE"
    availability: str  # "AVAILABLE", "UNAVAILABLE", "UNKNOWN"
    primary_ip: str = ""
    groups: List[str] = Field(default_factory=list)
    datacenter: Optional[str] = None
    rack: Optional[str] = None
    os: Optional[str] = None
    active_problems_count: int = 0
    cpu_util: Optional[float] = None
    memory_util: Optional[float] = None
    storage_util: Optional[float] = None
    interfaces: List[HostInterfaceDTO] = Field(default_factory=list)


class Host360ListResponseDTO(BaseModel):
    items: List[Host360ListItemDTO]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    generated_at: str


class Host360DetailDTO(BaseModel):
    host_id: str
    name: str
    technical_name: str
    status: str  # "UP", "DOWN", "MAINTENANCE"
    overall_availability: str  # "AVAILABLE", "UNAVAILABLE", "UNKNOWN"
    groups: List[str] = Field(default_factory=list)
    interfaces: List[HostInterfaceDTO] = Field(default_factory=list)
    telemetry: HostHardwareTelemetryDTO = Field(default_factory=HostHardwareTelemetryDTO)
    inventory: Dict[str, Any] = Field(default_factory=dict)
    tags: List[Dict[str, str]] = Field(default_factory=list)
    active_problems: List[HostProblemEventDTO] = Field(default_factory=list)
    maintenance: Optional[Dict[str, Any]] = None
    data_lineage: Dict[str, Any] = Field(default_factory=dict)
    generated_at: str


class TelemetrySeriesPointDTO(BaseModel):
    clock: int
    timestamp_iso: str
    value: Optional[float] = None


class Host360TelemetryResponseDTO(BaseModel):
    host_id: str
    host_name: str
    time_range: str
    time_from: int
    time_till: int
    series: Dict[str, List[TelemetrySeriesPointDTO]]  # "cpu", "memory", "storage"
    generated_at: str
