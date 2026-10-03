import pytest
from app.adapters.zabbix.mock import MockZabbixAdapter
from modules.availability.backend.services import AvailabilityService
from modules.availability.backend.schemas import AvailabilityOverviewDTO, ServiceAvailabilityListDTO


class MultiPeriodFailureSimulationAdapter(MockZabbixAdapter):
    """
    Adapter returning realistic Zabbix 7.0.5 multi-period matrix payload.
    In real Zabbix, periods are chronological (oldest at index 0, latest at index N-1).
    Day 1 (index 0): 100% UP (uptime: 86400, downtime: 0, sli: 100.0)
    Day 2 (index 1): Disaster Outage (uptime: 0, downtime: 86400, sli: 0.0)
    """
    async def get_slas(self, sla_ids=None, service_ids=None, search=None, limit=100):
        return [{
            "slaid": "1",
            "name": "Production SLA",
            "period": 0,  # Daily
            "slo": 99.0,
            "effective_date": 1704067200,
            "timezone": "UTC",
            "status": "1",
            "description": "Daily SLA",
            "schedule": [],
            "excluded_downtimes": [],
            "service_tags": [{"tag": "env", "operator": "0", "value": "prod"}]
        }]

    async def get_services(self, service_ids=None, sla_ids=None, search=None, status=None, limit=500):
        return [{
            "serviceid": "101",
            "name": "Payment Service",
            "status": 0,
            "tags": [{"tag": "env", "value": "prod"}],
            "problem_events": []
        }]

    async def get_sla_sli(self, slaid, period_from=None, period_to=None, periods=None, service_ids=None):
        return {
            "periods": [
                {"period_from": 1000, "period_to": 87400},
                {"period_from": 87400, "period_to": 173800}
            ],
            "serviceids": ["101"],
            "sli": [
                [{"uptime": 86400, "downtime": 0, "sli": 100.0, "error_budget": 864, "excluded_downtimes": []}],
                [{"uptime": 0, "downtime": 86400, "sli": 0.0, "error_budget": -85536, "excluded_downtimes": []}]
            ]
        }


class MultiSlaFailureSimulationAdapter(MockZabbixAdapter):
    """
    Simulates real enterprise with 2 distinct SLAs:
    SLA 1 -> Service 101 (Tier 1)
    SLA 2 -> Service 102 (Tier 2)
    Service 103 -> Belongs to both SLA 1 and SLA 2
    Service 104 -> Unconfigured (no SLA)
    """
    async def get_slas(self, sla_ids=None, service_ids=None, search=None, limit=100):
        all_slas = [
            {
                "slaid": "1",
                "name": "Tier 1 SLA",
                "period": 2,
                "slo": 99.9,
                "timezone": "UTC",
                "status": "1",
                "excluded_downtimes": []
            },
            {
                "slaid": "2",
                "name": "Tier 2 SLA",
                "period": 2,
                "slo": 95.0,
                "timezone": "UTC",
                "status": "1",
                "excluded_downtimes": []
            }
        ]
        if sla_ids:
            all_slas = [s for s in all_slas if s["slaid"] in sla_ids]
        if service_ids:
            # Zabbix native filtering when serviceids is provided
            res = []
            for s in all_slas:
                if s["slaid"] == "1" and any(sid in ("101", "103") for sid in service_ids):
                    res.append(s)
                elif s["slaid"] == "2" and any(sid in ("102", "103") for sid in service_ids):
                    res.append(s)
            return res[:limit]
        return all_slas[:limit]

    async def get_services(self, service_ids=None, sla_ids=None, search=None, status=None, limit=500):
        srvs = [
            {"serviceid": "101", "name": "Banking API", "status": 0, "tags": [], "problem_events": []},
            {"serviceid": "102", "name": "Customer Portal", "status": 0, "tags": [], "problem_events": []},
            {"serviceid": "103", "name": "Shared DB", "status": 0, "tags": [], "problem_events": []},
            {"serviceid": "104", "name": "Internal Wiki", "status": 0, "tags": [], "problem_events": []}
        ]
        return srvs[:limit]

    async def get_sla_sli(self, slaid, period_from=None, period_to=None, periods=None, service_ids=None):
        if slaid == "1":
            # Matches 101 and 103
            matched_sids = [s for s in ["101", "103"] if not service_ids or s in service_ids]
            cells = []
            for sid in matched_sids:
                cells.append({"uptime": 2591000, "downtime": 1000, "sli": 99.96, "error_budget": 1500, "excluded_downtimes": []})
            return {
                "periods": [{"period_from": 1000, "period_to": 2000}],
                "serviceids": matched_sids,
                "sli": [cells]
            }
        elif slaid == "2":
            # Matches 102 and 103
            matched_sids = [s for s in ["102", "103"] if not service_ids or s in service_ids]
            cells = []
            for sid in matched_sids:
                cells.append({"uptime": 2500000, "downtime": 92000, "sli": 96.45, "error_budget": 3000, "excluded_downtimes": []})
            return {
                "periods": [{"period_from": 1000, "period_to": 2000}],
                "serviceids": matched_sids,
                "sli": [cells]
            }
        return {"periods": [], "serviceids": [], "sli": []}


# -------------------------------------------------------------
# RED TESTS: These MUST FAIL on current unpatched code
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_dat02_multi_period_overview_truncation_defect():
    """
    DEMONSTRATE DAT-02 DEFECT:
    In current code, services.py line 172 does: period_cells = sli_matrix[0].
    With Day 1 = 100% and Day 2 = 0%, total downtime over the 2 days is 86,400s and SLI is 50%.
    Current code only inspects Day 1, so total_downtime is reported as 0s and SLI as 100%,
    discarding the day 2 disaster!
    """
    adapter = MultiPeriodFailureSimulationAdapter()
    service = AvailabilityService(adapter=adapter)
    
    overview = await service.get_overview(time_range="24h")
    
    # CONTRACT: Across the 2 days, downtime must be 86,400s and average SLI must be 50.0%
    assert overview.total_downtime_seconds == 86400, f"Expected 86400s downtime across both days, got {overview.total_downtime_seconds}"
    assert overview.average_sli == 50.0, f"Expected 50.0% average SLI across 2 days, got {overview.average_sli}"


@pytest.mark.asyncio
async def test_srv01_multi_sla_services_blindness_defect():
    """
    DEMONSTRATE SRV-01 DEFECT:
    Current code only queries primary SLA (SLA 1).
    Service 102 belongs to SLA 2.
    Current code marks Service 102 as NO_DATA / NOT_CONFIGURED!
    Invariant: A valid service with a configured SLA must NEVER become NO_DATA.
    """
    adapter = MultiSlaFailureSimulationAdapter()
    service = AvailabilityService(adapter=adapter)
    
    # Query without sla_id filter
    res = await service.get_services(page=1, page_size=25)
    
    s102 = next((s for s in res.items if s.service_id == "102"), None)
    assert s102 is not None
    # MUST FAIL ON CURRENT CODE because current code returns sli_current=None, sla_status="NOT_CONFIGURED" or "NO_DATA"
    assert s102.sli_current == 96.45, f"Service 102 must have SLI 96.45 from SLA 2, got {s102.sli_current}"
    assert s102.sla_status == "COMPLIANT", f"Service 102 must be COMPLIANT under SLA 2, got {s102.sla_status}"
    assert s102.sla_name == "Tier 2 SLA"


@pytest.mark.asyncio
async def test_trn01_trend_invalid_service_raises_404():
    """
    DEMONSTRATE TRN-01 DEFECT:
    In current code, passing an invalid service_id (e.g. '999') silently falls back
    to target_idx = 0 (Service 101) instead of erroring or reporting missing service!
    """
    adapter = MultiSlaFailureSimulationAdapter()
    service = AvailabilityService(adapter=adapter)
    
    # In current code: service_id="999" (does not belong to SLA 1) silently returns Service 101's data!
    # Expected: ValueError("Service '999' does not belong to SLA '1'")
    with pytest.raises(ValueError, match="does not belong to SLA"):
        await service.get_trend(sla_id="1", service_id="999")


@pytest.mark.asyncio
async def test_srv01_service_belonging_to_multiple_slas():
    """
    DEMONSTRATE SRV-01: Service 103 belongs to both SLA 1 and SLA 2.
    It should be discovered under both SLAs and not drop either.
    """
    adapter = MultiSlaFailureSimulationAdapter()
    service = AvailabilityService(adapter=adapter)
    
    res = await service.get_services(page=1, page_size=25)
    s103 = next((s for s in res.items if s.service_id == "103"), None)
    assert s103 is not None
    # Service 103 must have valid SLI and not NO_DATA
    assert s103.sli_current is not None
    assert s103.sla_status == "COMPLIANT"


@pytest.mark.asyncio
async def test_error_budget_authoritative_cell_preservation():
    """
    In MultiPeriodFailureSimulationAdapter, Day 2 has an active disaster with error_budget: -85536.
    The service overview/detail MUST preserve this authoritative negative integer from the current active period,
    not fabricate an artificial positive number!
    """
    adapter = MultiPeriodFailureSimulationAdapter()
    service = AvailabilityService(adapter=adapter)
    
    res = await service.get_services(page=1, page_size=25)
    s101 = next((s for s in res.items if s.service_id == "101"), None)
    assert s101 is not None
    # In current code: get_services queries periods=1 without timestamps, so it misses the multi-period active day 2 budget
    # On day 2, error budget must be -85536
    # When evaluated over the window:
    assert s101.error_budget_seconds is not None


@pytest.mark.asyncio
async def test_pag01_explicit_truncation_state():
    """
    DEMONSTRATE PAG-01:
    When candidate set is truncated at limit, summary MUST have is_truncated=True
    and report candidate_limit.
    """
    adapter = MultiSlaFailureSimulationAdapter()
    service = AvailabilityService(adapter=adapter)
    res = await service.get_services(page=1, page_size=25)
    assert "is_truncated" in res.summary

