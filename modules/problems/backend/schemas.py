from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProblemHostDTO(BaseModel):
    hostid: str
    host: str
    name: str


class ProblemTagDTO(BaseModel):
    tag: str
    value: str


class ProblemAcknowledgeDTO(BaseModel):
    acknowledgeid: str
    userid: str
    clock: int
    time: str
    message: str
    action: str


class ProblemAlertDTO(BaseModel):
    alertid: str
    mediatypeid: str
    clock: int
    time: str
    sendto: str
    status: str
    error: str


class ProblemItemDTO(BaseModel):
    eventid: str
    severity: int
    severity_name: str
    name: str
    clock: int
    start_time: str
    duration_seconds: int
    duration_human: str
    acknowledged: bool
    suppressed: bool
    suppression_data: List[Dict[str, Any]] = []
    opdata: str
    cause_eventid: Optional[str] = None
    is_cause: bool = True
    is_symptom: bool = False
    hosts: List[ProblemHostDTO] = []
    host_groups: List[str] = []
    tags: List[ProblemTagDTO] = []
    acknowledges: List[ProblemAcknowledgeDTO] = []


class ProblemDetailResponseDTO(ProblemItemDTO):
    alerts: List[ProblemAlertDTO] = []


class ProblemSeveritySummaryDTO(BaseModel):
    disaster: int = 0
    high: int = 0
    average: int = 0
    warning: int = 0
    information: int = 0
    unclassified: int = 0


class ProblemListSummaryDTO(BaseModel):
    total_problems: int
    by_severity: ProblemSeveritySummaryDTO
    acknowledged_count: int
    unacknowledged_count: int
    suppressed_count: int
    mtta_seconds: Optional[float] = None
    mtta_human: str = "NO_DATA"
    generated_at: str


class ProblemListResponseDTO(BaseModel):
    items: List[ProblemItemDTO]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    summary: ProblemListSummaryDTO


class ProblemFilterParams(BaseModel):
    page: int = 1
    page_size: int = 25
    time_from: Optional[int] = None
    time_till: Optional[int] = None
    severities: Optional[List[int]] = None
    acknowledged: Optional[bool] = None
    suppressed: Optional[bool] = None
    search: Optional[str] = None
    group: Optional[str] = None
    host: Optional[str] = None
    sort: str = "clock"
    sortorder: str = "DESC"
