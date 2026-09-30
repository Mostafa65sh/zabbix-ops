from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProblemCountSummary(BaseModel):
    total: int = 0
    disaster: int = 0
    high: int = 0
    average: int = 0
    warning: int = 0
    information: int = 0


class InterfaceModel(BaseModel):
    interfaceid: str
    ip: str = ""
    dns: str = ""
    port: str = ""
    type: int = 1
    main: int = 1
    available: int = 0


class HostSummary(BaseModel):
    id: str
    name: str
    status: str  # "UP", "DOWN", "MAINTENANCE", "UNKNOWN"
    groups: List[str] = Field(default_factory=list)
    interfaces: List[InterfaceModel] = Field(default_factory=list)
    tags: List[Dict[str, str]] = Field(default_factory=list)
    maintenance: Optional[str] = None
    problem_summary: ProblemCountSummary = Field(default_factory=ProblemCountSummary)


class ProblemItem(BaseModel):
    eventid: str
    severity: int
    name: str
    clock: int
    acknowledged: bool
    host_id: Optional[str] = None
    host_name: Optional[str] = None


class OverviewData(BaseModel):
    hosts_total: int
    hosts_available: int
    hosts_down: int
    hosts_maintenance: int
    problems_active: int
    problems_by_severity: ProblemCountSummary
    availability_pct: float


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str
    zabbix_adapter: str
    zabbix_connected: bool
