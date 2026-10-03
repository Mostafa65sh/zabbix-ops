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


# 9. Valid 100% and Compliance Semantics
@pytest.mark.asyncio
async def test_valid_compliant_and_breached_semantics():
    adapter = MockZabbixAdapter()
    service = AvailabilityService(adapter=adapter)
    res = await service.get_services(page=1, page_size=100)

    # Core Banking: compliant
    core = next((s for s in res.items if s.service_id == "service_01"), None)
    assert core is not None
    assert core.sla_status == "COMPLIANT"
    assert core.sli_current == 99.98
    assert core.sli_formatted == "99.98%"
    assert "+" in core.error_budget_formatted

    # Customer Portal: breached due to active problem
    portal = next((s for s in res.items if s.service_id == "service_02"), None)
    assert portal is not None
    assert portal.sla_status == "BREACHED"
    assert portal.status == "HIGH"
    assert portal.problem_count >= 1
    assert portal.sli_current == 98.85
    assert "-" in core.error_budget_formatted or "-" in portal.error_budget_formatted


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


# 14. Call budget: Overview <= 3 calls (Target: 2 calls)
@pytest.mark.asyncio
async def test_call_budget_overview():
    spy = AdapterCallSpy(MockZabbixAdapter())
    service = AvailabilityService(adapter=spy)
    await service.get_overview()

    assert len(spy.call_history) <= 3
    assert len(spy.call_history) == 2
    called_methods = [c["method"] for c in spy.call_history]
    assert "get_slas" in called_methods
    assert "get_services" in called_methods


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
