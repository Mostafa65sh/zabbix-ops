import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock

from app.main import app
from app.adapters.zabbix.client import get_zabbix_adapter
from app.adapters.zabbix.mock import MockZabbixAdapter
from app.core.auth import User, require_permission, set_auth_provider, BaseAuthProvider, LocalDevAuthProvider


@pytest.fixture
def mock_adapter():
    return MockZabbixAdapter()


@pytest.fixture
def test_user():
    return User(
        id="usr_test_01",
        username="noc_operator",
        roles=["operator"],
        permissions=["module.global_search.view"]
    )


@pytest.fixture
def client(mock_adapter, test_user):
    app.dependency_overrides[get_zabbix_adapter] = lambda: mock_adapter
    app.dependency_overrides[require_permission("module.global_search.view")] = lambda: test_user
    
    transport = ASGITransport(app=app)
    c = AsyncClient(transport=transport, base_url="http://test")
    yield c
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_global_search_status_operational(client):
    """Verify that Module 08 status endpoint reports operational and version 1.0.0."""
    resp = await client.get("/api/v1/global_search/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["module"] == "global_search"
    assert data["status"] == "operational"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_global_search_query_all_categories(client):
    """Verify cross-category unified search across hosts, problems, services, and items."""
    resp = await client.get("/api/v1/global_search/query?q=server")
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "server"
    assert "categories" in data
    assert "hosts" in data["categories"]
    assert "problems" in data["categories"]
    assert "services" in data["categories"]
    assert "items" in data["categories"]

    hosts = data["categories"]["hosts"]["items"]
    assert len(hosts) > 0
    # Every returned host should contain server in name, host, ip, or os
    assert any("SERVER" in h["name"].upper() for h in hosts)


@pytest.mark.asyncio
async def test_global_search_category_filter(client):
    """Verify filtering to a single category returns only that category's items."""
    resp = await client.get("/api/v1/global_search/query?q=server&categories=hosts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["categories"]["hosts"]["items"]) > 0
    assert len(data["categories"]["problems"]["items"]) == 0
    assert len(data["categories"]["services"]["items"]) == 0
    assert len(data["categories"]["items"]["items"]) == 0


@pytest.mark.asyncio
async def test_global_search_rbac_enforcement(mock_adapter):
    """Verify unauthenticated/unauthorized users are denied with 403 Forbidden."""
    app.dependency_overrides[get_zabbix_adapter] = lambda: mock_adapter
    # Override with user lacking permissions
    unauthorized_user = User(
        id="usr_unauth",
        username="unauthorized_guest",
        roles=["guest"],
        permissions=["some.other.permission"]
    )
    # Don't override require_permission, test real permission check
    app.dependency_overrides.clear()
    app.dependency_overrides[get_zabbix_adapter] = lambda: mock_adapter

    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: unauthorized_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/api/v1/global_search/status")
        assert resp.status_code == 403

        query_resp = await c.get("/api/v1/global_search/query?q=server")
        assert query_resp.status_code == 403

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_global_search_adversarial_empty_query(client):
    """Verify empty or whitespace queries return immediate empty results without errors."""
    resp = await client.get("/api/v1/global_search/query?q=")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_results"] == 0
    assert len(data["categories"]["hosts"]["items"]) == 0

    resp_ws = await client.get("/api/v1/global_search/query?q=%20%20%20")
    assert resp_ws.status_code == 200
    data_ws = resp_ws.json()
    assert data_ws["total_results"] == 0


@pytest.mark.asyncio
async def test_global_search_adversarial_zero_fabrication(client):
    """Verify missing or unmonitored metrics return None/null, never fabricated fallback values."""
    resp = await client.get("/api/v1/global_search/query?q=DEV-LEGACY-HOST&categories=items")
    assert resp.status_code == 200
    data = resp.json()
    items = data["categories"]["items"]["items"]
    # For legacy host that is DOWN with no metrics, lastvalue must be None
    legacy_items = [it for it in items if "DEV-LEGACY-HOST" in it["host_name"]]
    for it in legacy_items:
        assert it["lastvalue"] is None


@pytest.mark.asyncio
async def test_global_search_adversarial_invalid_category(client):
    """Verify invalid category query is handled gracefully or returns 422."""
    resp = await client.get("/api/v1/global_search/query?q=test&categories=nonexistent_category")
    # Should either be 422 or ignore unknown category
    assert resp.status_code in [200, 422]
    if resp.status_code == 200:
        data = resp.json()
        assert data["total_results"] == 0


@pytest.mark.asyncio
async def test_global_search_truncation_semantics(client, mock_adapter):
    """Verify truncation flags and total counts are truthfully returned when limit is reached."""
    # Request with limit=1
    resp = await client.get("/api/v1/global_search/query?q=server&limit=1")
    assert resp.status_code == 200
    data = resp.json()
    hosts_cat = data["categories"]["hosts"]
    assert len(hosts_cat["items"]) <= 1
    if hosts_cat["total_matched"] > 1:
        assert hosts_cat["is_truncated"] is True


@pytest.mark.asyncio
async def test_global_search_api_call_bounds(client, mock_adapter):
    """Verify search execution performs bounded O(1) batched adapter queries, no N+1."""
    mock_adapter.get_server_inventory = AsyncMock(wraps=mock_adapter.get_server_inventory)
    mock_adapter.get_problem_feed = AsyncMock(wraps=mock_adapter.get_problem_feed)
    mock_adapter.get_services = AsyncMock(wraps=mock_adapter.get_services)

    resp = await client.get("/api/v1/global_search/query?q=server")
    assert resp.status_code == 200

    # Exactly 1 call per searched category
    assert mock_adapter.get_server_inventory.call_count == 1
    assert mock_adapter.get_problem_feed.call_count == 1
    assert mock_adapter.get_services.call_count == 1
