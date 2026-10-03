import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.adapters.zabbix.mock import MockZabbixAdapter
from app.core.auth import User, set_auth_provider, BaseAuthProvider, LocalDevAuthProvider
from modules.top_n.backend.schemas import (
    TopNStatusResponse,
    TopNItemDTO,
    TopNResponseDTO,
    TopNOverviewResponseDTO
)


class RestrictedTopNAuthProvider(BaseAuthProvider):
    async def authenticate(self, credentials: dict):
        return None

    async def get_user_by_id(self, user_id: str):
        # User without module.top_n.view permission
        return User(
            id="usr_restricted_top_n",
            username="restricted_user",
            is_superuser=False,
            roles=["viewer"],
            permissions=["module.overview.view"]
        )


# ------------------------------------------------------------------
# RED TESTS: These must FAIL on current skeleton code
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_top_n_status_operational():
    """
    Skeleton returns status: 'skeleton' and version: '0.1.0'.
    Operational contract requires status: 'operational' and version: '1.0.0'.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/top_n/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "top_n"
        assert data["status"] == "operational"
        assert data["version"] == "1.0.0"
        assert data["declared_permission"] == "module.top_n.view"


@pytest.mark.asyncio
async def test_top_n_ranked_query():
    """
    Querying top N ranked hosts for a metric (e.g., cpu, memory, storage)
    must return sorted ranking with valid host metadata and zero-fabrication metrics.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/top_n/rankings?metric=cpu&limit=5&order=desc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["metric"] == "cpu"
        assert "items" in data
        assert len(data["items"]) >= 1
        first = data["items"][0]
        assert "rank" in first
        assert first["rank"] == 1
        assert "host_id" in first
        assert "host_name" in first
        assert "metric_value" in first


@pytest.mark.asyncio
async def test_top_n_overview_cards():
    """
    Top N overview dashboard endpoint returning top 5 leaders across all 4 key dimensions:
    CPU, Memory, Storage, and Problems.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/top_n/overview?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "cpu" in data
        assert "memory" in data
        assert "storage" in data
        assert "problems" in data
        assert len(data["cpu"]) <= 5
        assert len(data["memory"]) <= 5


@pytest.mark.asyncio
async def test_top_n_rbac_enforcement():
    """
    User lacking module.top_n.view receives HTTP 403 Forbidden.
    """
    set_auth_provider(RestrictedTopNAuthProvider())
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/top_n/rankings?metric=cpu")
            assert resp.status_code == 403
    finally:
        set_auth_provider(LocalDevAuthProvider())


@pytest.mark.asyncio
async def test_top_n_adversarial_invalid_metric():
    """
    Querying unsupported metric returns HTTP 422 validation error.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/top_n/rankings?metric=invalid_metric_xyz")
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_top_n_adversarial_zero_fabrication_unmonitored():
    """
    Hosts with missing/unmonitored metrics must report NO_DATA and None value,
    never fabricating 0% or 100%.
    """
    from modules.top_n.backend.services import TopNService
    mock_adapter = MockZabbixAdapter()
    service = TopNService(adapter=mock_adapter)

    metric_res = service._normalize_metric(None)
    assert metric_res.value is None
    assert metric_res.formatted == "NO_DATA"
    assert metric_res.status == "NO_DATA"


@pytest.mark.asyncio
async def test_top_n_adversarial_empty_group():
    """
    Filtering by a non-existent group returns 0 items and 0 evaluated hosts.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/top_n/rankings?metric=cpu&group=non_existent_group_xyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total_evaluated_hosts"] == 0


@pytest.mark.asyncio
async def test_top_n_truncation_semantics():
    """
    When candidate inventory hits 1000 nodes, is_truncated is True and
    truncation_reason is populated.
    """
    from unittest.mock import AsyncMock
    from modules.top_n.backend.services import TopNService

    mock_adapter = MockZabbixAdapter()
    fake_1000_hosts = [
        {
            "hostid": str(10000 + i),
            "name": f"HOST-{i}",
            "host": f"host-{i}.corp",
            "status": "UP",
            "interfaces": [],
            "groups": ["Linux Servers"],
            "metrics": {"cpu_util": 50.0 + (i % 30)}
        }
        for i in range(1000)
    ]
    mock_adapter.get_server_inventory = AsyncMock(return_value=fake_1000_hosts)
    mock_adapter.get_problems = AsyncMock(return_value=[])

    service = TopNService(adapter=mock_adapter)
    res = await service.get_rankings(metric="cpu", limit=10)

    assert res.is_truncated is True
    assert res.truncation_reason is not None
    assert "exceeds 1000 hosts" in res.truncation_reason
    assert res.total_evaluated_hosts == 1000
    assert len(res.items) == 10


@pytest.mark.asyncio
async def test_top_n_api_call_bounds():
    """
    Prove exact call counts for top N rankings query.
    Ensures O(1) query complexity without N+1 requests.
    """
    from unittest.mock import AsyncMock
    from modules.top_n.backend.services import TopNService

    mock_adapter = MockZabbixAdapter()
    mock_adapter.get_server_inventory = AsyncMock(wraps=mock_adapter.get_server_inventory)
    mock_adapter.get_problems = AsyncMock(wraps=mock_adapter.get_problems)

    service = TopNService(adapter=mock_adapter)
    res = await service.get_rankings(metric="cpu", limit=10)

    assert res is not None
    assert mock_adapter.get_server_inventory.call_count == 1
    assert mock_adapter.get_problems.call_count == 1

