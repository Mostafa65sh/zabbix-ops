import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.adapters.zabbix.mock import MockZabbixAdapter
from app.core.auth import User, set_auth_provider, BaseAuthProvider, LocalDevAuthProvider
from modules.host360.backend.schemas import Host360DetailDTO, Host360TelemetryResponseDTO


class RestrictedHost360AuthProvider(BaseAuthProvider):
    async def authenticate(self, credentials: dict):
        return None

    async def get_user_by_id(self, user_id: str):
        # User without module.host360.view permission
        return User(
            id="usr_restricted_host360",
            username="restricted_user",
            is_superuser=False,
            roles=["viewer"],
            permissions=["module.overview.view"]
        )


# ------------------------------------------------------------------
# RED TESTS: These must FAIL on current skeleton code
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_host360_status_operational():
    """
    Current code returns status: 'skeleton' and version: '0.1.0'.
    Contract requires operational status with version: '1.0.0'.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/host360/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "host360"
        assert data["status"] == "operational"
        assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_host360_list_hosts():
    """
    Host 360 selection endpoint listing searchable monitored hosts.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/host360/hosts?search=APP-01")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        host = data["items"][0]
        assert host["name"] == "SERVER-APP-01"
        assert host["host_id"] == "10001"
        assert "interfaces" in host


@pytest.mark.asyncio
async def test_host360_detail_endpoint():
    """
    Host 360 comprehensive profile endpoint.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/host360/10001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["host_id"] == "10001"
        assert data["name"] == "SERVER-APP-01"
        assert "telemetry" in data
        assert "interfaces" in data
        assert "inventory" in data
        assert "active_problems" in data


@pytest.mark.asyncio
async def test_host360_telemetry_history():
    """
    Host 360 time-series history endpoint for metric graphs.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/host360/10001/telemetry?time_range=24h")
        assert resp.status_code == 200
        data = resp.json()
        assert data["host_id"] == "10001"
        assert "series" in data
        assert "cpu" in data["series"]
        assert "memory" in data["series"]
        assert "storage" in data["series"]


@pytest.mark.asyncio
async def test_host360_not_found_404():
    """
    Querying invalid host ID returns 404.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/host360/non_existent_host_99999")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_host360_rbac_enforcement():
    """
    User lacking module.host360.view permission receives HTTP 403.
    """
    set_auth_provider(RestrictedHost360AuthProvider())
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/host360/10001")
            assert resp.status_code == 403
    finally:
        set_auth_provider(LocalDevAuthProvider())


@pytest.mark.asyncio
async def test_host360_adversarial_empty_search():
    """
    Search with no matching hosts returns empty items list, valid total_count 0.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/host360/hosts?search=non_existent_host_string_xyz_999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total_count"] == 0
        assert data["total_pages"] == 1


@pytest.mark.asyncio
async def test_host360_adversarial_time_ranges():
    """
    Test multiple valid time ranges and verify 422 on invalid time range pattern.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Valid windows
        for window in ["1h", "6h", "12h", "24h", "7d", "30d"]:
            resp = await client.get(f"/api/v1/host360/10001/telemetry?time_range={window}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["time_range"] == window
            assert "series" in data

        # Invalid window pattern
        resp_invalid = await client.get("/api/v1/host360/10001/telemetry?time_range=999y")
        assert resp_invalid.status_code == 422


@pytest.mark.asyncio
async def test_host360_adversarial_zero_fabrication_on_null_metrics():
    """
    Verify that when an unknown host has missing metric items,
    the service returns NO_DATA and None value, NEVER fabricating 0% or 100%.
    """
    from modules.host360.backend.services import Host360Service
    adapter = MockZabbixAdapter()
    service = Host360Service(adapter=adapter)
    
    # Direct normalization check
    metric_none = service._normalize_metric(None)
    assert metric_none.value is None
    assert metric_none.formatted == "NO_DATA"
    assert metric_none.status == "NO_DATA"

    metric_invalid = service._normalize_metric("invalid_string_val")
    assert metric_invalid.value is None
    assert metric_invalid.formatted == "NO_DATA"
    assert metric_invalid.status == "NO_DATA"


@pytest.mark.asyncio
async def test_host360_truncation_semantics_explicit():
    """
    Verify that when candidate inventory hits 1000 nodes, is_truncated is True
    and truncation_reason is explicitly populated.
    """
    from modules.host360.backend.services import Host360Service
    from unittest.mock import AsyncMock

    mock_adapter = MockZabbixAdapter()
    # Simulate 1000 hosts returned from adapter
    fake_1000_hosts = [
        {
            "hostid": str(10000 + i),
            "name": f"HOST-{i}",
            "host": f"host-{i}.corp",
            "status": "UP",
            "interfaces": [],
            "groups": ["Linux Servers"],
            "metrics": {}
        }
        for i in range(1000)
    ]
    mock_adapter.get_server_inventory = AsyncMock(return_value=fake_1000_hosts)
    mock_adapter.get_problems = AsyncMock(return_value=[])

    service = Host360Service(adapter=mock_adapter)
    res = await service.list_hosts(page=1, page_size=25)

    assert res.is_truncated is True
    assert res.truncation_reason is not None
    assert "exceeds 1000 hosts" in res.truncation_reason
    assert res.total_count == 1000
    assert len(res.items) == 25


@pytest.mark.asyncio
async def test_host360_drilldown_exact_api_call_counts():
    """
    Prove exact call counts for host detail and telemetry history endpoints.
    Ensures O(1) bounded queries and zero hidden N+1 behavior.
    """
    from unittest.mock import AsyncMock
    from modules.host360.backend.services import Host360Service

    mock_adapter = MockZabbixAdapter()
    mock_adapter.get_server_inventory = AsyncMock(wraps=mock_adapter.get_server_inventory)
    mock_adapter.get_problems = AsyncMock(wraps=mock_adapter.get_problems)
    mock_adapter.get_host_telemetry_history = AsyncMock(wraps=mock_adapter.get_host_telemetry_history)

    service = Host360Service(adapter=mock_adapter)

    # 1. Host 360 Detail
    detail = await service.get_host_360_detail("10001")
    assert detail is not None
    assert mock_adapter.get_server_inventory.call_count == 1
    assert mock_adapter.get_problems.call_count == 1

    # 2. Telemetry Series
    mock_adapter.get_server_inventory.reset_mock()
    mock_adapter.get_problems.reset_mock()

    telemetry = await service.get_host_telemetry_series("10001", time_range="24h")
    assert telemetry is not None
    # get_host_telemetry_series calls get_host_360_detail (1 inventory, 1 problem) + 1 get_host_telemetry_history
    assert mock_adapter.get_server_inventory.call_count == 1
    assert mock_adapter.get_problems.call_count == 1
    assert mock_adapter.get_host_telemetry_history.call_count == 1

