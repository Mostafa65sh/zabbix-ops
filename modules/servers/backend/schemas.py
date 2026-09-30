from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ServerMetricValue(BaseModel):
    value: Optional[float] = None
    formatted: str = "NO_DATA"
    status: str = "NO_DATA"  # "NORMAL", "WARNING", "CRITICAL", "NO_DATA"
    unit: str = "%"


class ServerHardwareDTO(BaseModel):
    cpu_utilization: ServerMetricValue = Field(default_factory=ServerMetricValue)
    cpu_cores: Optional[int] = None
    cpu_load: Optional[float] = None
    memory_utilization: ServerMetricValue = Field(default_factory=ServerMetricValue)
    memory_total_bytes: Optional[int] = None
    memory_used_bytes: Optional[int] = None
    storage_utilization: ServerMetricValue = Field(default_factory=ServerMetricValue)
    storage_total_bytes: Optional[int] = None
    storage_used_bytes: Optional[int] = None


class ServerNetworkInterfaceDTO(BaseModel):
    interfaceid: str
    ip: str = ""
    dns: str = ""
    port: str = "10050"
    type: str = "AGENT"  # "AGENT", "SNMP", "IPMI", "JMX"
    is_main: bool = True
    availability: str = "UNKNOWN"  # "AVAILABLE", "UNAVAILABLE", "UNKNOWN"
    error: Optional[str] = None
    traffic_in: Optional[str] = None
    traffic_out: Optional[str] = None


class ServerProblemSummaryDTO(BaseModel):
    total: int = 0
    disaster: int = 0
    high: int = 0
    average: int = 0
    warning: int = 0
    information: int = 0
    highest_severity: Optional[int] = None


class ServerItemDTO(BaseModel):
    id: str
    name: str
    technical_name: str
    status: str  # "UP", "DOWN", "MAINTENANCE", "UNKNOWN"
    overall_availability: str  # "AVAILABLE", "UNAVAILABLE", "UNKNOWN"
    ip: str = ""
    os: str = "Unknown OS"
    os_type: str = "unknown"  # "linux", "windows", "network", "other", "unknown"
    hardware_summary: str = "Standard Compute"
    hardware: ServerHardwareDTO = Field(default_factory=ServerHardwareDTO)
    interfaces: List[ServerNetworkInterfaceDTO] = Field(default_factory=list)
    groups: List[str] = Field(default_factory=list)
    tags: List[Dict[str, str]] = Field(default_factory=list)
    datacenter: Optional[str] = None
    rack: Optional[str] = None
    environment: Optional[str] = None
    maintenance_name: Optional[str] = None
    problems: ServerProblemSummaryDTO = Field(default_factory=ServerProblemSummaryDTO)
    last_updated: str
    data_lineage: Dict[str, str] = Field(default_factory=dict)


class ServerListSummaryDTO(BaseModel):
    total_servers: int = 0
    servers_up: int = 0
    servers_down: int = 0
    servers_maintenance: int = 0
    available_count: int = 0
    unavailable_count: int = 0
    unknown_count: int = 0
    avg_cpu_percent: Optional[float] = None
    avg_memory_percent: Optional[float] = None
    avg_storage_percent: Optional[float] = None


class ServerFilterParams(BaseModel):
    search: Optional[str] = None
    group: Optional[str] = None
    status: Optional[str] = None
    availability: Optional[str] = None
    os_type: Optional[str] = None
    datacenter: Optional[str] = None
    has_problems: Optional[bool] = None
    severity: Optional[int] = None
    page: int = 1
    page_size: int = 25
    sort_by: str = "name"
    sort_order: str = "asc"


class ServerListResponseDTO(BaseModel):
    items: List[ServerItemDTO]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    summary: ServerListSummaryDTO
    applied_filters: Dict[str, Any]
    generated_at: str


class ServerDetailResponseDTO(BaseModel):
    server: ServerItemDTO
    inventory: Dict[str, Any] = Field(default_factory=dict)
    active_problems: List[Dict[str, Any]] = Field(default_factory=list)
    metrics_breakdown: Dict[str, Any] = Field(default_factory=dict)
    generated_at: str
