import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "0.1.0"
        assert data["zabbix_connected"] is True
        assert data["zabbix_adapter"] == "mock"


@pytest.mark.asyncio
async def test_overview_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/overview")
        assert response.status_code == 200
        data = response.json()
        assert "hosts_total" in data
        assert "availability_pct" in data
        assert data["hosts_total"] > 0
        assert data["availability_pct"] >= 0.0


@pytest.mark.asyncio
async def test_hosts_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/hosts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        first_host = data[0]
        assert "id" in first_host
        assert "name" in first_host
        assert "status" in first_host
        assert "problem_summary" in first_host


@pytest.mark.asyncio
async def test_problems_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/problems")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            first_p = data[0]
            assert "eventid" in first_p
            assert "severity" in first_p
            assert "name" in first_p
