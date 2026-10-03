import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from modules.availability.backend.schemas import (
    AvailabilityOverviewDTO,
    ServiceAvailabilityListDTO,
    SLAListResponseDTO,
    AvailabilityTrendResponseDTO
)
from modules.availability.backend.services import AvailabilityService
from app.adapters.zabbix.mock import MockZabbixAdapter
from app.adapters.zabbix.real import RealZabbixAdapter
from app.core.auth import User, set_auth_provider, BaseAuthProvider, LocalDevAuthProvider


class RestrictedAvailabilityAuthProvider(BaseAuthProvider):
    async def authenticate(self, credentials: dict):
        return None

    async def get_user_by_id(self, user_id: str):
        # User lacking module.availability.view permission
        return User(
            id="usr_restricted_avail",
            username="restricted_avail_user",
            is_superuser=False,
            roles=["viewer"],
            permissions=["module.overview.view", "module.servers.view"]
        )


class AdapterCallSpy:
    """Spy wrapper around ZabbixAdapterBase to trace calls, count, and verify no offset."""
    def __init__(self, target_adapter):
        self._target = target_adapter
        self.call_history = []

    def __getattr__(self, name):
        attr = getattr(self._target, name)
        if callable(attr):
            async def wrapper(*args, **kwargs):
                self.call_history.append({"method": name, "args": args, "kwargs": kwargs})
                return await attr(*args, **kwargs)
            return wrapper
        return attr


# 1. Endpoint 200 - Overview
@pytest.mark.asyncio
async def test_availability_overview_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/availability/")
        assert resp.status_code == 200
        data = resp.json()
        validated = AvailabilityOverviewDTO(**data)
        assert validated.total_services >= 4
        assert validated.total_slas >= 2
        assert validated.overall_status in ("OK", "DEGRADED", "CRITICAL", "NO_DATA")
        assert validated.average_sli is not None
        assert "%" in validated.average_sli_formatted


# 2. Endpoint 200 - Services list
@pytest.mark.asyncio
async def test_services_list_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/availability/services")
        assert resp.status_code == 200
        data = resp.json()
        validated = ServiceAvailabilityListDTO(**data)
        assert validated.total_count >= 4
        assert len(validated.items) >= 4
        assert validated.page == 1


# 3. Endpoint 200 - SLAs list
@pytest.mark.asyncio
async def test_slas_list_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/availability/slas")
        assert resp.status_code == 200
        data = resp.json()
        validated = SLAListResponseDTO(**data)
        assert validated.total_count >= 2
        assert len(validated.items) >= 2


# 4. Endpoint 200 - Trend
@pytest.mark.asyncio
async def test_availability_trend_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/availability/trend?sla_id=sla_01&periods=6")
        assert resp.status_code == 200
        data = resp.json()
        validated = AvailabilityTrendResponseDTO(**data)
        assert validated.sla_id == "sla_01"
        assert len(validated.points) == 6
        for pt in validated.points:
            assert pt.period_from > 0
            assert pt.period_to > pt.period_from


# 5. Endpoint 200 - Status
@pytest.mark.asyncio
async def test_availability_status_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/availability/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "availability"
        assert data["status"] == "operational"
        assert data["version"] == "1.0.0"


# 6. RBAC 403 Forbidden
@pytest.mark.asyncio
async def test_availability_rbac_forbidden():
    set_auth_provider(RestrictedAvailabilityAuthProvider())
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/availability/")
            assert resp.status_code == 403
            assert "Permission denied" in resp.json()["detail"]

            resp_srv = await client.get("/api/v1/availability/services")
            assert resp_srv.status_code == 403

            resp_sla = await client.get("/api/v1/availability/slas")
            assert resp_sla.status_code == 403

            resp_tr = await client.get("/api/v1/availability/trend?sla_id=sla_01")
            assert resp_tr.status_code == 403
    finally:
        set_auth_provider(LocalDevAuthProvider())


# 7. Invalid parameters validation
@pytest.mark.asyncio
async def test_invalid_parameters():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid time preset
        resp = await client.get("/api/v1/availability/?time_range=invalid_preset")
        assert resp.status_code == 422

        # Invalid sort_by
        resp2 = await client.get("/api/v1/availability/services?sort_by=unsupported_field")
        assert resp2.status_code == 422

        # Invalid sort_order
        resp3 = await client.get("/api/v1/availability/services?sort_order=UPPERCASE")
        assert resp3.status_code == 422

        # Non-existent SLA in trend -> 404
        resp4 = await client.get("/api/v1/availability/trend?sla_id=non_existent_sla")
        assert resp4.status_code == 404


# 8. NO_DATA and NOT_CONFIGURED semantics
@pytest.mark.asyncio
async def test_no_data_and_not_configured_semantics():
    adapter = MockZabbixAdapter()
    service = AvailabilityService(adapter=adapter)
    res = await service.get_services(page=1, page_size=100)

    # service_04 is the sandbox cluster without SLA
    sandbox = next((s for s in res.items if s.service_id == "service_04"), None)
    assert sandbox is not None
    assert sandbox.sla_status == "NOT_CONFIGURED"
    assert sandbox.sli_current is None
    assert sandbox.sli_formatted == "NO_DATA"
    assert sandbox.error_budget_formatted == "NO_DATA"


# 9. Valid 100% and Compliance Semantics (Golden Rule: Zero Fabrication)
@pytest.mark.asyncio
async def test_valid_compliant_and_breached_semantics():
    adapter = MockZabbixAdapter()
    service = AvailabilityService(adapter=adapter)
    
    # Untargeted query (evaluates primary SLA)
    res = await service.get_services(page=1, page_size=100)

    # Core Banking: compliant under primary SLA
    core = next((s for s in res.items if s.service_id == "service_01"), None)
    assert core is not None
    assert core.sla_status == "COMPLIANT"
    assert core.sli_current == 99.98
    assert core.sli_formatted == "99.98%"
    assert "+" in core.error_budget_formatted

    # Customer Portal is linked to sla_02. In untargeted query, it returns NO_DATA (never fabricated fallback numbers!)
    portal_unscoped = next((s for s in res.items if s.service_id == "service_02"), None)
    assert portal_unscoped is not None
    assert portal_unscoped.sla_status == "NO_DATA"
    assert portal_unscoped.sli_current is None
    assert portal_unscoped.sli_formatted == "NO_DATA"

    # When explicitly targeted with sla_id="sla_02", Customer Portal's real Zabbix SLI is retrieved
    res_targeted = await service.get_services(page=1, page_size=100, sla_id="sla_02")
    portal = next((s for s in res_targeted.items if s.service_id == "service_02"), None)
    assert portal is not None
    assert portal.sla_status == "BREACHED"
    assert portal.status == "HIGH"
    assert portal.problem_count >= 1
    assert portal.sli_current == 98.85
    assert "-" in portal.error_budget_formatted


# 10. Excluded downtime / Planned maintenance
@pytest.mark.asyncio
async def test_excluded_downtime_maintenance():
    adapter = MockZabbixAdapter()
    service = AvailabilityService(adapter=adapter)
    overview = await service.get_overview()
    assert overview.total_excluded_downtime_seconds > 0

    slas = await service.get_slas()
    sla_fin = next((s for s in slas.items if s.sla_id == "sla_01"), None)
    assert sla_fin is not None
    assert len(sla_fin.excluded_downtimes) >= 1
    assert "Maintenance" in sla_fin.excluded_downtimes[0].name


# 11. Pagination & Slicing
@pytest.mark.asyncio
async def test_pagination_and_slicing():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/availability/services?page=1&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] >= 2


# 12. Search and status filtering
@pytest.mark.asyncio
async def test_search_and_status_filtering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Search by keyword
        resp_search = await client.get("/api/v1/availability/services?search=banking")
        assert resp_search.status_code == 200
        items = resp_search.json()["items"]
        assert len(items) >= 1
        assert "Banking" in items[0]["name"]

        # Filter by status
        resp_status = await client.get("/api/v1/availability/services?status=HIGH")
        assert resp_status.status_code == 200
        for it in resp_status.json()["items"]:
            assert it["status"] == "HIGH"


# 13. Sorting options
@pytest.mark.asyncio
async def test_sorting_options():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Sort by name asc
        resp_name = await client.get("/api/v1/availability/services?sort_by=name&sort_order=asc")
        assert resp_name.status_code == 200
        names = [x["name"] for x in resp_name.json()["items"]]
        assert names == sorted(names)


# 14. Call budget: Overview <= 3 calls
@pytest.mark.asyncio
async def test_call_budget_overview():
    spy = AdapterCallSpy(MockZabbixAdapter())
    service = AvailabilityService(adapter=spy)
    await service.get_overview()

    assert len(spy.call_history) <= 3
    called_methods = [c["method"] for c in spy.call_history]
    assert "get_slas" in called_methods
    assert "get_services" in called_methods
    assert "get_sla_sli" in called_methods


# 15. Call budget: Services list <= 3 calls
@pytest.mark.asyncio
async def test_call_budget_services_list():
    spy = AdapterCallSpy(MockZabbixAdapter())
    service = AvailabilityService(adapter=spy)
    await service.get_services(page=1, page_size=25, sla_id="sla_01")

    assert len(spy.call_history) <= 3
    called_methods = [c["method"] for c in spy.call_history]
    assert "get_services" in called_methods


# 16. Call budget: SLAs list <= 3 calls (Target: 1-2 calls)
@pytest.mark.asyncio
async def test_call_budget_slas_list():
    spy = AdapterCallSpy(MockZabbixAdapter())
    service = AvailabilityService(adapter=spy)
    await service.get_slas(page=1, page_size=25)

    assert len(spy.call_history) <= 3


# 17. Call budget: Trend <= 3 calls (Target: 2 calls)
@pytest.mark.asyncio
async def test_call_budget_trend():
    spy = AdapterCallSpy(MockZabbixAdapter())
    service = AvailabilityService(adapter=spy)
    await service.get_trend(sla_id="sla_01", periods=12)

    assert len(spy.call_history) <= 3
    assert len(spy.call_history) == 2


# 18. N+1 prevention: No unbounded loop over SLAs
@pytest.mark.asyncio
async def test_n_plus_one_prevention():
    spy = AdapterCallSpy(MockZabbixAdapter())
    service = AvailabilityService(adapter=spy)
    # Requesting services list across all SLAs
    await service.get_services(page=1, page_size=50)

    # Total calls must remain <= 3, never 1 per service or 1 per SLA!
    assert len(spy.call_history) <= 3
    sli_calls = sum(1 for c in spy.call_history if c["method"] == "get_sla_sli")
    assert sli_calls <= 1


# 19. RealZabbixAdapter parameter validation: NO offset
@pytest.mark.asyncio
async def test_real_adapter_zero_offset_enforcement():
    real_adapter = RealZabbixAdapter(api_url="http://dummy:80/api_jsonrpc.php", api_token="dummy_token")
    recorded_payloads = []

    # Monkeypatch _call_api to inspect outgoing JSON-RPC payload
    async def fake_call_api(method: str, params: dict):
        recorded_payloads.append({"method": method, "params": params})
        if method == "sla.get":
            return []
        if method == "service.get":
            return []
        if method == "sla.getsli":
            return {"periods": [], "serviceids": [], "sli": []}
        return []

    real_adapter._call_api = fake_call_api

    await real_adapter.get_slas(limit=50)
    await real_adapter.get_services(limit=100)
    await real_adapter.get_sla_sli(slaid="1")

    # Strict check: "offset" must NOT appear in any params!
    for rec in recorded_payloads:
        assert "offset" not in rec["params"], f"Forbidden 'offset' found in {rec['method']} call!"
        assert "limit" in rec["params"] or rec["method"] == "sla.getsli"


# 20. Empty query handling
@pytest.mark.asyncio
async def test_empty_query_handling():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/availability/services?search=NonExistentKeywordXYZ")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == 0
        assert data["items"] == []
        assert data["page"] == 1


# 21. Real Numeric SLA IDs: "1", "2", "15" must NOT become NO_DATA
class NumericIdTestAdapter(MockZabbixAdapter):
    """Adapter simulating real Zabbix 7.0.5 dynamic numeric IDs."""
    async def get_slas(self, sla_ids=None, service_ids=None, search=None, limit=100):
        all_slas = [
            {
                "slaid": "1",
                "name": "Production Tier-1 SLA",
                "period": 2,
                "slo": 99.90,
                "effective_date": 1704067200,
                "timezone": "UTC",
                "status": "1",
                "description": "Production numeric SLA 1",
                "schedule": [],
                "excluded_downtimes": [],
                "service_tags": [{"tag": "env", "operator": "0", "value": "prod"}]
            },
            {
                "slaid": "2",
                "name": "Internal Tools SLA",
                "period": 2,
                "slo": 95.00,
                "effective_date": 1704067200,
                "timezone": "UTC",
                "status": "1",
                "description": "Production numeric SLA 2",
                "schedule": [],
                "excluded_downtimes": [],
                "service_tags": [{"tag": "env", "operator": "0", "value": "internal"}]
            },
            {
                "slaid": "15",
                "name": "Data Analytics SLA",
                "period": 2,
                "slo": 99.00,
                "effective_date": 1704067200,
                "timezone": "UTC",
                "status": "1",
                "description": "Production numeric SLA 15",
                "schedule": [],
                "excluded_downtimes": [],
                "service_tags": [{"tag": "env", "operator": "0", "value": "analytics"}]
            }
        ]
        if sla_ids:
            all_slas = [s for s in all_slas if s["slaid"] in sla_ids]
        return all_slas[:limit]

    async def get_services(self, service_ids=None, sla_ids=None, search=None, status=None, limit=500):
        srvs = [
            {"serviceid": "101", "name": "Payment Gateway", "status": 0, "tags": [{"tag": "env", "value": "prod"}], "problem_events": []},
            {"serviceid": "102", "name": "Zero Uptime Outage", "status": 5, "tags": [{"tag": "env", "value": "prod"}], "problem_events": []},
            {"serviceid": "103", "name": "Perfect Uptime Service", "status": 0, "tags": [{"tag": "env", "value": "prod"}], "problem_events": []},
            {"serviceid": "104", "name": "Internal Wiki", "status": 0, "tags": [{"tag": "env", "value": "internal"}], "problem_events": []},
            {"serviceid": "105", "name": "Unconfigured Service", "status": 0, "tags": [{"tag": "env", "value": "standalone"}], "problem_events": []}
        ]
        return srvs[:limit]

    async def get_sla_sli(self, slaid, period_from=None, period_to=None, periods=None, service_ids=None):
        if slaid == "1":
            return {
                "periods": [{"period_from": period_from or 1000, "period_to": period_to or 2000}],
                "serviceids": ["101", "102", "103"],
                "sli": [
                    [
                        {"uptime": 2591000, "downtime": 1000, "sli": 99.95, "error_budget": 1200, "excluded_downtimes": []},
                        {"uptime": 0, "downtime": 2592000, "sli": 0.0, "error_budget": -24000, "excluded_downtimes": []},
                        {"uptime": 2592000, "downtime": 0, "sli": 100.0, "error_budget": 2592, "excluded_downtimes": []}
                    ]
                ]
            }
        return {"periods": [], "serviceids": [], "sli": []}


@pytest.mark.asyncio
async def test_numeric_sla_ids_do_not_become_no_data():
    adapter = NumericIdTestAdapter()
    service = AvailabilityService(adapter=adapter)
    
    # 1. Verify get_slas handles numeric IDs "1", "2", "15"
    slas_res = await service.get_slas()
    sla_1 = next((s for s in slas_res.items if s.sla_id == "1"), None)
    assert sla_1 is not None, "Numeric SLA '1' must be resolved!"
    assert sla_1.current_sli is not None, "Numeric SLA '1' must NOT be converted to NO_DATA!"
    assert sla_1.sli_formatted == "99.98%" or "%" in sla_1.sli_formatted
    assert sla_1.service_count == 3

    # 2. Verify get_services handles numeric IDs and preserves 0.0 and 100.0
    services_res = await service.get_services(page=1, page_size=10, sla_id="1")
    
    # Service 101: 99.95%
    s101 = next((s for s in services_res.items if s.service_id == "101"), None)
    assert s101 is not None
    assert s101.sli_current == 99.95
    assert s101.sli_formatted == "99.95%"
    assert s101.sla_status == "COMPLIANT"

    # Service 102: Valid 0.0% outage MUST remain 0.0%, never NO_DATA or 100%
    s102 = next((s for s in services_res.items if s.service_id == "102"), None)
    assert s102 is not None
    assert s102.sli_current == 0.0
    assert s102.sli_formatted == "0.00%"
    assert s102.sla_status == "BREACHED"

    # Service 103: Valid 100.0% MUST remain 100.0%
    s103 = next((s for s in services_res.items if s.service_id == "103"), None)
    assert s103 is not None
    assert s103.sli_current == 100.0
    assert s103.sli_formatted == "100.00%"
    assert s103.sla_status == "COMPLIANT"

    # Service 105: No linked SLA MUST return NOT_CONFIGURED
    s105 = next((s for s in services_res.items if s.service_id == "105"), None)
    assert s105 is not None
    assert s105.sla_status == "NOT_CONFIGURED"
    assert s105.sli_current is None
    assert s105.sli_formatted == "NO_DATA"
    assert s105.error_budget_formatted == "NO_DATA"


# 22. Pagination test for exact dataset sizes: 25, 26, 50, 51, 100, 500
class PaginationDatasetAdapter(MockZabbixAdapter):
    def __init__(self, count: int):
        super().__init__()
        self.count = count

    async def get_services(self, service_ids=None, sla_ids=None, search=None, status=None, limit=500):
        effective_count = min(self.count, limit)
        return [
            {
                "serviceid": f"srv_{i:04d}",
                "name": f"Service Record {i:04d}",
                "status": 0,
                "tags": [{"tag": "env", "value": "prod"}],
                "problem_events": []
            }
            for i in range(1, effective_count + 1)
        ]


@pytest.mark.asyncio
async def test_pagination_dataset_sizes():
    for dataset_size in (25, 26, 50, 51, 100, 500):
        adapter = PaginationDatasetAdapter(count=dataset_size)
        service = AvailabilityService(adapter=adapter)

        # Page 1
        page1 = await service.get_services(page=1, page_size=25)
        assert page1.total_count == dataset_size, f"Failed total_count for dataset {dataset_size} on page 1"
        expected_pages = (dataset_size + 24) // 25
        assert page1.total_pages == expected_pages, f"Failed total_pages for dataset {dataset_size}"
        assert len(page1.items) == min(25, dataset_size)
        assert page1.page == 1

        # When dataset > 25, verify Page 2 exists, is disjoint from Page 1, and Next is valid
        if dataset_size > 25:
            page2 = await service.get_services(page=2, page_size=25)
            assert page2.total_count == dataset_size
            assert page2.total_pages == expected_pages
            assert page2.page == 2
            expected_page2_len = min(25, dataset_size - 25)
            assert len(page2.items) == expected_page2_len

            page1_ids = {item.service_id for item in page1.items}
            page2_ids = {item.service_id for item in page2.items}
            assert len(page1_ids.intersection(page2_ids)) == 0, "Page 1 and Page 2 must contain disjoint items!"


# 23. Time range presets produce distinct operational windows passed to adapter
@pytest.mark.asyncio
async def test_time_range_presets_produce_distinct_windows():
    spy = AdapterCallSpy(MockZabbixAdapter())
    service = AvailabilityService(adapter=spy)

    windows = {}
    for preset in ("24h", "7d", "30d", "90d", "365d"):
        spy.call_history.clear()
        res = await service.get_overview(time_range=preset)
        sli_call = next((c for c in spy.call_history if c["method"] == "get_sla_sli"), None)
        assert sli_call is not None, f"get_sla_sli must be called for preset {preset}"
        p_from = sli_call["kwargs"].get("period_from")
        p_to = sli_call["kwargs"].get("period_to")
        assert p_from is not None and p_to is not None
        window_duration = p_to - p_from
        windows[preset] = window_duration

    # Verify all window durations are strictly increasing and match operational presets
    assert windows["24h"] == 86400
    assert windows["7d"] == 604800
    assert windows["30d"] == 2592000
    assert windows["90d"] == 7776000
    assert windows["365d"] == 31536000


# 24. Custom time range application
@pytest.mark.asyncio
async def test_custom_time_range_application():
    spy = AdapterCallSpy(MockZabbixAdapter())
    service = AvailabilityService(adapter=spy)

    t_from = 1700000000
    t_till = 1700500000
    res = await service.get_overview(time_from=t_from, time_till=t_till)

    sli_call = next((c for c in spy.call_history if c["method"] == "get_sla_sli"), None)
    assert sli_call is not None
    assert sli_call["kwargs"]["period_from"] == t_from
    assert sli_call["kwargs"]["period_to"] == t_till
    assert "Custom" in res.measured_period


# 25. Static Verification: Zero mock SLA IDs or fabricated values in production services.py
def test_static_zero_mock_coupling_or_data_fabrication_in_service():
    import inspect
    from modules.availability.backend import services

    source = inspect.getsource(services)
    
    # Forbidden mock identifiers in production logic
    forbidden_tokens = [
        "sla_01",
        "sla_02",
        "2591480",
        "2562192",
        "29808",
        "16848",
        "2072"
    ]
    for token in forbidden_tokens:
        assert token not in source, f"Forbidden mock token or fabricated value '{token}' found in services.py!"


# 26. Call budget strictly <= 3 on all endpoints
@pytest.mark.asyncio
async def test_call_budget_strictly_enforced_on_all_endpoints():
    spy = AdapterCallSpy(MockZabbixAdapter())
    service = AvailabilityService(adapter=spy)

    # 1. Overview
    spy.call_history.clear()
    await service.get_overview()
    assert len(spy.call_history) <= 3

    # 2. Services List
    spy.call_history.clear()
    await service.get_services(page=1, page_size=50)
    assert len(spy.call_history) <= 3

    # 3. SLAs List
    spy.call_history.clear()
    await service.get_slas(page=1, page_size=25)
    assert len(spy.call_history) <= 3

    # 4. Trend
    spy.call_history.clear()
    await service.get_trend(sla_id="sla_01", periods=12)
    assert len(spy.call_history) <= 3

