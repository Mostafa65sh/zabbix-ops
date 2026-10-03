import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.adapters.zabbix.mock import MockZabbixAdapter
from app.core.auth import User, set_auth_provider, BaseAuthProvider, LocalDevAuthProvider
from modules.graph_explorer.backend.schemas import (
    GraphExplorerStatusResponse,
    GraphMetricSeriesDTO,
    MultiSeriesGraphResponseDTO
)


class RestrictedGraphExplorerAuthProvider(BaseAuthProvider):
    async def authenticate(self, credentials: dict):
        return None

    async def get_user_by_id(self, user_id: str):
        # User without module.graph_explorer.view permission
        return User(
            id="usr_restricted_graph",
            username="restricted_user",
            is_superuser=False,
            roles=["viewer"],
            permissions=["module.overview.view"]
        )


# ------------------------------------------------------------------
# RED TESTS: These must FAIL on current skeleton code
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_graph_explorer_status_operational():
    """
    Current code returns status: 'skeleton' and version: '0.1.0'.
    Operational contract requires status: 'operational' and version: '1.0.0'.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/graph_explorer/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "graph_explorer"
        assert data["status"] == "operational"
        assert data["version"] == "1.0.0"
        assert data["declared_permission"] == "module.graph_explorer.view"


@pytest.mark.asyncio
async def test_graph_explorer_metrics_query():
    """
    Multi-series telemetry query comparing metrics across hosts and metrics.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/graph_explorer/series?host_ids=10001,10002&metrics=cpu,memory&time_range=24h")
        assert resp.status_code == 200
        data = resp.json()
        assert "series" in data
        assert len(data["series"]) >= 2
        first = data["series"][0]
        assert "series_id" in first
        assert "host_id" in first
        assert "metric_name" in first
        assert "points" in first
        assert len(first["points"]) > 0


@pytest.mark.asyncio
async def test_graph_explorer_hosts_options():
    """
    Endpoint providing available host targets with their available metrics for multi-series selection.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/graph_explorer/targets")
        assert resp.status_code == 200
        data = resp.json()
        assert "targets" in data
        assert len(data["targets"]) >= 1
        tgt = data["targets"][0]
        assert "host_id" in tgt
        assert "host_name" in tgt
        assert "available_metrics" in tgt


@pytest.mark.asyncio
async def test_graph_explorer_rbac_enforcement():
    """
    User lacking module.graph_explorer.view permission receives HTTP 403.
    """
    set_auth_provider(RestrictedGraphExplorerAuthProvider())
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/graph_explorer/series?host_ids=10001&metrics=cpu")
            assert resp.status_code == 403
    finally:
        set_auth_provider(LocalDevAuthProvider())


@pytest.mark.asyncio
async def test_graph_explorer_adversarial_invalid_metric():
    """
    Querying invalid/unsupported metric returns HTTP 422 validation error.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/graph_explorer/series?host_ids=10001&metrics=invalid_metric_xyz")
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_graph_explorer_zero_fabrication():
    """
    Missing data in series points must be explicitly None, never fabricated.
    """
    from modules.graph_explorer.backend.services import GraphExplorerService
    adapter = MockZabbixAdapter()
    service = GraphExplorerService(adapter=adapter)

    # Empty/unknown host produces empty points or None values, never fabricated numbers
    res = await service.get_multi_series(host_ids=["99999"], metrics=["cpu"], time_range="24h")
    assert res is not None
    assert len(res.series) == 0 or all(p.value is None for s in res.series for p in s.points)


@pytest.mark.asyncio
async def test_graph_explorer_adversarial_empty_targets():
    """
    Search with non-existent target keyword returns empty targets list.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/graph_explorer/targets?search=non_existent_host_string_999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["targets"] == []
        assert data["total_targets"] == 0


@pytest.mark.asyncio
async def test_graph_explorer_truncation_semantics():
    """
    When candidate hosts hit 1000 nodes, is_truncated is True and
    truncation_reason is explicitly populated.
    """
    from unittest.mock import AsyncMock
    from modules.graph_explorer.backend.services import GraphExplorerService

    mock_adapter = MockZabbixAdapter()
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

    service = GraphExplorerService(adapter=mock_adapter)
    res = await service.get_targets()

    assert res.is_truncated is True
    assert res.truncation_reason is not None
    assert "exceeds 1000 hosts" in res.truncation_reason
    assert res.total_targets == 1000


@pytest.mark.asyncio
async def test_graph_explorer_call_bounds():
    """
    Ensure exact API calls for series extraction: 1 inventory call + exactly 1 telemetry call per requested host.
    """
    from unittest.mock import AsyncMock
    from modules.graph_explorer.backend.services import GraphExplorerService

    mock_adapter = MockZabbixAdapter()
    mock_adapter.get_server_inventory = AsyncMock(wraps=mock_adapter.get_server_inventory)
    mock_adapter.get_host_telemetry_history = AsyncMock(wraps=mock_adapter.get_host_telemetry_history)

    service = GraphExplorerService(adapter=mock_adapter)
    res = await service.get_multi_series(host_ids=["10001", "10002"], metrics=["cpu", "memory"])

    assert res is not None
    assert mock_adapter.get_server_inventory.call_count == 1
    assert mock_adapter.get_host_telemetry_history.call_count == 2

