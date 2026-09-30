import pytest
import time
from httpx import AsyncClient, ASGITransport

from app.main import app
from modules.problems.backend.schemas import (
    ProblemListResponseDTO,
    ProblemDetailResponseDTO,
    ProblemListSummaryDTO,
    ProblemFilterParams
)
from modules.problems.backend.services import ProblemsService
from app.adapters.zabbix.mock import MockZabbixAdapter
from app.adapters.zabbix.real import RealZabbixAdapter
from app.core.auth import User, set_auth_provider, LocalDevAuthProvider, BaseAuthProvider


class RestrictedProblemsAuthProvider(BaseAuthProvider):
    async def authenticate(self, credentials: dict):
        return None

    async def get_user_by_id(self, user_id: str):
        # User lacking module.problems.view permission
        return User(
            id="usr_restricted_prob",
            username="restricted_prob_user",
            is_superuser=False,
            roles=["viewer"],
            permissions=["module.overview.view", "module.servers.view"]
        )


# 1. Problem list endpoint
@pytest.mark.asyncio
async def test_problem_list_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems")
        assert resp.status_code == 200
        data = resp.json()
        validated = ProblemListResponseDTO(**data)
        assert validated.total_count >= 8
        assert len(validated.items) >= 8
        assert validated.page == 1


# 2. DTO validation
@pytest.mark.asyncio
async def test_dto_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems")
        assert resp.status_code == 200
        data = resp.json()
        validated = ProblemListResponseDTO(**data)
        for item in validated.items:
            assert isinstance(item.eventid, str) and item.eventid
            assert 0 <= item.severity <= 5
            assert item.severity_name in ("DISASTER", "HIGH", "AVERAGE", "WARNING", "INFORMATION", "UNCLASSIFIED")
            assert isinstance(item.clock, int) and item.clock > 0
            assert item.start_time != "NO_DATA"
            assert isinstance(item.duration_seconds, int)
            assert item.duration_human != ""
            assert isinstance(item.acknowledged, bool)
            assert isinstance(item.suppressed, bool)
            assert item.opdata != ""
            assert isinstance(item.is_cause, bool)
            assert isinstance(item.is_symptom, bool)


# 3. Severity filtering
@pytest.mark.asyncio
async def test_severity_filtering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems?severities=4,5")
        assert resp.status_code == 200
        data = resp.json()
        validated = ProblemListResponseDTO(**data)
        for item in validated.items:
            assert item.severity in (4, 5)


# 4. Acknowledgment filtering
@pytest.mark.asyncio
async def test_acknowledgment_filtering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Acknowledged only
        resp_ack = await client.get("/api/v1/problems?acknowledged=true")
        assert resp_ack.status_code == 200
        for item in resp_ack.json()["items"]:
            assert item["acknowledged"] is True

        # Unacknowledged only
        resp_unack = await client.get("/api/v1/problems?acknowledged=false")
        assert resp_unack.status_code == 200
        for item in resp_unack.json()["items"]:
            assert item["acknowledged"] is False


# 5. Suppression filtering
@pytest.mark.asyncio
async def test_suppression_filtering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp_supp = await client.get("/api/v1/problems?suppressed=true")
        assert resp_supp.status_code == 200
        items = resp_supp.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert item["suppressed"] is True


# 6. Time range filtering
@pytest.mark.asyncio
async def test_time_range_filtering():
    now = int(time.time())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Filter problems in last 1 hour
        time_from = now - 3600
        resp = await client.get(f"/api/v1/problems?time_from={time_from}&time_till={now}")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["clock"] >= time_from


# 7. Host filtering
@pytest.mark.asyncio
async def test_host_filtering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems?host=BORDER-GATEWAY-01")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert any("border-gateway-01" in h["name"].lower() or "border-gateway-01" in h["host"].lower() for h in item["hosts"])


# 8. Host group filtering
@pytest.mark.asyncio
async def test_host_group_filtering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems?group=network")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data


# 9. Keyword search
@pytest.mark.asyncio
async def test_keyword_search():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems?search=WAN")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert "wan" in item["name"].lower() or any("wan" in h["name"].lower() for h in item["hosts"])


# 10. Pagination
@pytest.mark.asyncio
async def test_pagination():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp_p1 = await client.get("/api/v1/problems?page=1&page_size=2")
        assert resp_p1.status_code == 200
        d1 = resp_p1.json()
        assert len(d1["items"]) == 2

        resp_p2 = await client.get("/api/v1/problems?page=2&page_size=2")
        assert resp_p2.status_code == 200
        d2 = resp_p2.json()
        assert len(d2["items"]) == 2

        # Page 1 items should differ from page 2 items
        p1_ids = [x["eventid"] for x in d1["items"]]
        p2_ids = [x["eventid"] for x in d2["items"]]
        assert set(p1_ids).isdisjoint(set(p2_ids))


# 11. Total count
@pytest.mark.asyncio
async def test_total_count():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems?page=1&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] >= 8


# 12. Total pages
@pytest.mark.asyncio
async def test_total_pages():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems?page=1&page_size=3")
        assert resp.status_code == 200
        data = resp.json()
        expected_pages = (data["total_count"] + 3 - 1) // 3
        assert data["total_pages"] == expected_pages


# 13. Sorting
@pytest.mark.asyncio
async def test_sorting():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Sort by severity descending
        resp_sev_desc = await client.get("/api/v1/problems?sort=severity&sortorder=DESC")
        assert resp_sev_desc.status_code == 200
        sevs_desc = [x["severity"] for x in resp_sev_desc.json()["items"]]
        assert sevs_desc == sorted(sevs_desc, reverse=True)

        # Sort by severity ascending
        resp_sev_asc = await client.get("/api/v1/problems?sort=severity&sortorder=ASC")
        assert resp_sev_asc.status_code == 200
        sevs_asc = [x["severity"] for x in resp_sev_asc.json()["items"]]
        assert sevs_asc == sorted(sevs_asc)


# 14. Empty results
@pytest.mark.asyncio
async def test_empty_results():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems?search=NONEXISTENT_KEYWORD_XYZ_12345")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total_count"] == 0
        assert data["total_pages"] == 1


# 15. Summary endpoint
@pytest.mark.asyncio
async def test_problems_summary():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems/summary")
        assert resp.status_code == 200
        data = resp.json()
        summary = ProblemListSummaryDTO(**data)
        assert summary.total_problems >= 8
        assert summary.acknowledged_count >= 1
        assert summary.unacknowledged_count >= 1
        assert summary.suppressed_count >= 1
        assert summary.by_severity.disaster >= 1
        assert summary.by_severity.high >= 1


# 16. MTTA calculation
@pytest.mark.asyncio
async def test_mtta_calculation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems/summary")
        assert resp.status_code == 200
        data = resp.json()
        # In mock data, there are acknowledged events with ack times
        assert data["mtta_seconds"] is not None
        assert data["mtta_seconds"] > 0
        assert data["mtta_human"] != "NO_DATA"


# 17. Zero acknowledged MTTA -> NO_DATA
@pytest.mark.asyncio
async def test_zero_acknowledged_mtta_no_data():
    class NoAckAdapter(MockZabbixAdapter):
        def _get_raw_mock_problems(self):
            # All unacknowledged
            probs = super()._get_raw_mock_problems()
            for p in probs:
                p["acknowledged"] = "0"
                p["acknowledges"] = []
            return probs

    service = ProblemsService(adapter=NoAckAdapter())
    summary = await service.get_summary()
    assert summary.mtta_seconds is None
    assert summary.mtta_human == "NO_DATA"


# 18. Cause / Symptom logic
@pytest.mark.asyncio
async def test_cause_symptom():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems")
        assert resp.status_code == 200
        items = resp.json()["items"]

        # 90002 is root cause
        p_cause = next(p for p in items if p["eventid"] == "90002")
        assert p_cause["is_cause"] is True
        assert p_cause["is_symptom"] is False
        assert p_cause["cause_eventid"] is None

        # 90004 is symptom of 90002
        p_symptom = next(p for p in items if p["eventid"] == "90004")
        assert p_symptom["is_cause"] is False
        assert p_symptom["is_symptom"] is True
        assert p_symptom["cause_eventid"] == "90002"


# 19. Detail endpoint
@pytest.mark.asyncio
async def test_detail_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems/90001")
        assert resp.status_code == 200
        detail = ProblemDetailResponseDTO(**resp.json())
        assert detail.eventid == "90001"
        assert detail.severity == 5
        assert len(detail.alerts) >= 1
        assert detail.alerts[0].sendto == "noc-alerts@company.internal"


# 20. 404 for nonexistent problem
@pytest.mark.asyncio
async def test_detail_404_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/problems/99999999")
        assert resp.status_code == 404


# 21. Permission 403 Forbidden
@pytest.mark.asyncio
async def test_permission_403_forbidden():
    set_auth_provider(RestrictedProblemsAuthProvider())
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp_list = await client.get("/api/v1/problems")
            assert resp_list.status_code == 403

            resp_sum = await client.get("/api/v1/problems/summary")
            assert resp_sum.status_code == 403

            resp_detail = await client.get("/api/v1/problems/90001")
            assert resp_detail.status_code == 403

            resp_status = await client.get("/api/v1/problems/status")
            assert resp_status.status_code == 403
    finally:
        set_auth_provider(LocalDevAuthProvider())


# 22. Real adapter parameter compliance
@pytest.mark.asyncio
async def test_real_adapter_parameter_compliance():
    recorded_calls = []

    class MockedRealZabbix(RealZabbixAdapter):
        def __init__(self):
            super().__init__(api_url="http://mocked-zabbix/api_jsonrpc.php", api_token="test_token")

        async def _call_api(self, method: str, params: dict):
            recorded_calls.append({"method": method, "params": params})
            if method == "problem.get":
                if params.get("countOutput"):
                    return 5
                return [
                    {
                        "eventid": "1",
                        "source": "0",
                        "object": "0",
                        "objectid": "10",
                        "clock": "1700000000",
                        "r_eventid": "0",
                        "r_clock": "0",
                        "name": "High load",
                        "acknowledged": "0",
                        "severity": "4",
                        "cause_eventid": "0",
                        "opdata": "5.4",
                        "suppressed": "0",
                        "hosts": [{"hostid": "100", "host": "h1", "name": "Host 1"}],
                        "tags": [],
                        "acknowledges": [],
                        "suppression_data": []
                    }
                ]
            elif method == "event.get":
                return [{"eventid": "1", "alerts": []}]
            return []

    adapter = MockedRealZabbix()
    service = ProblemsService(adapter=adapter)
    res = await service.get_problems(ProblemFilterParams(page=1, page_size=10))

    assert res.total_count == 5
    assert len(res.items) == 1

    # Check outgoing JSON-RPC calls
    assert len(recorded_calls) == 2
    count_call = recorded_calls[0]
    feed_call = recorded_calls[1]

    assert count_call["method"] == "problem.get"
    assert count_call["params"]["countOutput"] is True
    assert count_call["params"]["recent"] is True

    assert feed_call["method"] == "problem.get"
    assert feed_call["params"]["recent"] is True


# 23. Real adapter NEVER sends offset to problem.get
@pytest.mark.asyncio
async def test_real_adapter_no_offset_parameter():
    recorded_calls = []

    class MockedRealZabbix(RealZabbixAdapter):
        def __init__(self):
            super().__init__(api_url="http://mocked-zabbix/api_jsonrpc.php", api_token="test_token")

        async def _call_api(self, method: str, params: dict):
            recorded_calls.append({"method": method, "params": params})
            return []

    adapter = MockedRealZabbix()
    await adapter.get_problem_feed(limit=25, offset=50)

    for call in recorded_calls:
        assert "offset" not in call["params"], "offset must NEVER be sent to Zabbix problem.get!"


# 24. CamelCase native Zabbix selectors
@pytest.mark.asyncio
async def test_real_adapter_camelcase_selectors():
    recorded_calls = []

    class MockedRealZabbix(RealZabbixAdapter):
        def __init__(self):
            super().__init__(api_url="http://mocked-zabbix/api_jsonrpc.php", api_token="test_token")

        async def _call_api(self, method: str, params: dict):
            recorded_calls.append({"method": method, "params": params})
            if method == "problem.get":
                return [{
                    "eventid": "100", "clock": "1700000000", "name": "Alarm", "severity": "3",
                    "hosts": [], "tags": [], "acknowledges": [], "suppression_data": []
                }]
            elif method == "event.get":
                return [{"eventid": "100", "alerts": []}]
            return []

    adapter = MockedRealZabbix()
    await adapter.get_problem_feed(limit=10, offset=0)
    await adapter.get_problem_detail("100")

    prob_calls = [c for c in recorded_calls if c["method"] == "problem.get"]
    for c in prob_calls:
        p = c["params"]
        assert "selectHosts" in p
        assert "selectTags" in p
        assert "selectAcknowledges" in p
        assert "selectSuppressionData" in p
        # Assert no snake_case selectors exist
        assert "select_hosts" not in p
        assert "select_tags" not in p
        assert "select_acknowledges" not in p
        assert "select_suppression_data" not in p

    event_calls = [c for c in recorded_calls if c["method"] == "event.get"]
    assert len(event_calls) == 1
    ev_p = event_calls[0]["params"]
    assert "selectAlerts" in ev_p
    assert "select_alerts" not in ev_p


# 25. Bounded API calls / Performance Test Gate
@pytest.mark.asyncio
async def test_performance_gate_call_counts():
    recorded_calls = []

    class CallCountingRealZabbix(RealZabbixAdapter):
        def __init__(self):
            super().__init__(api_url="http://mocked-zabbix/api_jsonrpc.php", api_token="test_token")

        async def _call_api(self, method: str, params: dict):
            recorded_calls.append({"method": method, "params": params})
            if method == "problem.get":
                if params.get("countOutput"):
                    return 20
                return [
                    {
                        "eventid": str(i), "clock": str(1700000000 + i), "name": f"Problem {i}",
                        "severity": "3", "hosts": [], "tags": [], "acknowledges": [], "suppression_data": []
                    }
                    for i in range(20)
                ]
            elif method == "event.get":
                return [{"eventid": "1", "alerts": []}]
            return []

    adapter = CallCountingRealZabbix()
    service = ProblemsService(adapter=adapter)

    # 1. List call: maximum 2 native API calls
    recorded_calls.clear()
    await service.get_problems(ProblemFilterParams(page=1, page_size=20))
    assert len(recorded_calls) <= 2, f"List made {len(recorded_calls)} calls (max 2 allowed)"

    # 2. Summary call: maximum 1 native API call
    recorded_calls.clear()
    await service.get_summary()
    assert len(recorded_calls) <= 1, f"Summary made {len(recorded_calls)} calls (max 1 allowed)"

    # 3. Detail call: maximum 2 native API calls
    recorded_calls.clear()
    await service.get_problem_detail("1")
    assert len(recorded_calls) <= 2, f"Detail made {len(recorded_calls)} calls (max 2 allowed)"


# 26. No per-row host.get
@pytest.mark.asyncio
async def test_no_per_row_host_get():
    recorded_calls = []

    class MockZabbix(RealZabbixAdapter):
        def __init__(self):
            super().__init__(api_url="http://mocked-zabbix/api_jsonrpc.php", api_token="test_token")

        async def _call_api(self, method: str, params: dict):
            recorded_calls.append(method)
            return []

    adapter = MockZabbix()
    service = ProblemsService(adapter=adapter)
    await service.get_problems(ProblemFilterParams())
    assert "host.get" not in recorded_calls


# 27. No per-row item.get
@pytest.mark.asyncio
async def test_no_per_row_item_get():
    recorded_calls = []

    class MockZabbix(RealZabbixAdapter):
        def __init__(self):
            super().__init__(api_url="http://mocked-zabbix/api_jsonrpc.php", api_token="test_token")

        async def _call_api(self, method: str, params: dict):
            recorded_calls.append(method)
            return []

    adapter = MockZabbix()
    service = ProblemsService(adapter=adapter)
    await service.get_problems(ProblemFilterParams())
    assert "item.get" not in recorded_calls


# 28. Mock/Real contract compatibility
@pytest.mark.asyncio
async def test_mock_and_real_contract_compatibility():
    mock_adapter = MockZabbixAdapter()
    mock_feed = await mock_adapter.get_problem_feed(limit=5)
    assert isinstance(mock_feed, list)
    for p in mock_feed:
        assert "eventid" in p
        assert "severity" in p
        assert "clock" in p
        assert "name" in p
        assert "hosts" in p
        assert "tags" in p
        assert "acknowledges" in p
        assert "suppression_data" in p


# 29. Module 01 regression
@pytest.mark.asyncio
async def test_module_01_regression():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "health" in data
        assert "hosts" in data
        assert "recent_events" in data


# 30. Module 02 regression
@pytest.mark.asyncio
async def test_module_02_regression():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/servers")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total_count" in data
        assert "summary" in data
