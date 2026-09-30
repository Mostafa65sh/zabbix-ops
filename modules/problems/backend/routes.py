from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.core.logging import get_module_logger
from app.core.auth import require_permission, User
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.adapters.zabbix.client import get_zabbix_adapter
from modules.problems.backend.schemas import (
    ProblemListResponseDTO,
    ProblemListSummaryDTO,
    ProblemDetailResponseDTO,
    ProblemFilterParams
)
from modules.problems.backend.services import ProblemsService

logger = get_module_logger("problems")
router = APIRouter()


@router.get("", response_model=ProblemListResponseDTO)
@router.get("/", response_model=ProblemListResponseDTO)
async def list_problems(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page (max 100)"),
    time_from: Optional[int] = Query(None, ge=0, description="Unix timestamp start of operational window"),
    time_till: Optional[int] = Query(None, ge=0, description="Unix timestamp end of operational window"),
    severities: Optional[str] = Query(None, description="Comma-separated severity levels (0 to 5)"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment state"),
    suppressed: Optional[bool] = Query(None, description="Filter by suppression/maintenance state"),
    search: Optional[str] = Query(None, max_length=100, description="Keyword search across problem name and host"),
    group: Optional[str] = Query(None, max_length=100, description="Host group name filter"),
    host: Optional[str] = Query(None, max_length=100, description="Host name filter"),
    sort: str = Query("clock", pattern="^(clock|severity|name|eventid)$", description="Field to sort by"),
    sortorder: str = Query("DESC", pattern="^(ASC|DESC|asc|desc)$", description="Sort direction"),
    user: User = Depends(require_permission("module.problems.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve real-time paginated list of active infrastructure problems and events.
    Applies native Zabbix filtering with two-stage bounded query and client-side slicing.
    """
    logger.info(f"User '{user.username}' queried Problems feed (page={page}, size={page_size}, search='{search}')")

    sev_list: Optional[List[int]] = None
    if severities:
        sev_list = []
        for s in severities.split(","):
            s_stripped = s.strip()
            if s_stripped.isdigit():
                val = int(s_stripped)
                if 0 <= val <= 5:
                    sev_list.append(val)

    filters = ProblemFilterParams(
        page=page,
        page_size=page_size,
        time_from=time_from,
        time_till=time_till,
        severities=sev_list,
        acknowledged=acknowledged,
        suppressed=suppressed,
        search=search,
        group=group,
        host=host,
        sort=sort,
        sortorder=sortorder.upper()
    )

    service = ProblemsService(adapter=adapter)
    return await service.get_problems(filters)


@router.get("/summary", response_model=ProblemListSummaryDTO)
async def get_problems_summary(
    time_from: Optional[int] = Query(None, ge=0, description="Unix timestamp start of operational window"),
    time_till: Optional[int] = Query(None, ge=0, description="Unix timestamp end of operational window"),
    search: Optional[str] = Query(None, max_length=100, description="Keyword search"),
    group: Optional[str] = Query(None, max_length=100, description="Host group filter"),
    host: Optional[str] = Query(None, max_length=100, description="Host name filter"),
    user: User = Depends(require_permission("module.problems.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve aggregate operational summary and MTTA metrics for active problems.
    Respects active operational time window and calculates MTTA only on acknowledged items.
    """
    logger.info(f"User '{user.username}' queried Problems summary (from={time_from}, till={time_till})")
    service = ProblemsService(adapter=adapter)
    return await service.get_summary(
        time_from=time_from,
        time_till=time_till,
        search=search,
        group=group,
        host=host
    )


@router.get("/status")
async def get_module_status(user: User = Depends(require_permission("module.problems.view"))):
    """
    Operational readiness check for Module 03 — Problems.
    """
    return {
        "module": "problems",
        "name": "Problems",
        "status": "operational",
        "version": "1.0.0",
        "declared_permission": "module.problems.view"
    }


@router.get("/{event_id}", response_model=ProblemDetailResponseDTO)
async def get_problem_detail(
    event_id: str,
    user: User = Depends(require_permission("module.problems.view")),
    adapter: ZabbixAdapterBase = Depends(get_zabbix_adapter)
):
    """
    Retrieve comprehensive 360-degree problem detail by event ID.
    Includes alert notification chronology, acknowledgment trail, tags, and cause/symptom link.
    """
    logger.info(f"User '{user.username}' queried problem detail for event '{event_id}'")

    # Basic sanitization
    clean_id = event_id.strip()
    if not clean_id.isalnum() or len(clean_id) > 32:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event ID format: '{event_id}'"
        )

    service = ProblemsService(adapter=adapter)
    detail = await service.get_problem_detail(clean_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem event with ID '{event_id}' was not found."
        )

    return detail
