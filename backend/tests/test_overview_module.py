import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.modules.manager import ModuleManager
from modules.overview.backend.schemas import OverviewResponseDTO, OverviewFilterParams
from modules.overview.backend.services import OverviewService
from app.adapters.zabbix.mock import MockZabbixAdapter
from app.core.auth import User, set_auth_provider, BaseAuthProvider


class RestrictedMockAuthProvider(BaseAuthProvider):
    async def authenticate(self, credentials: dict):
        return None

    async def get_user_by_id(self, user_id: str):
        # User without module.overview.view permission
        return User(
            id="usr_restricted",
            username="restricted_user",
            is_superuser=False,
            roles=["viewer"],
            permissions=[]
        )


@pytest.mark.asyncio
async def test_overview_endpoint_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/overview")
        assert response.status_code == 200
        data = response.json()

        # Validate with Pydantic schema
        validated = OverviewResponseDTO(**data)
        assert validated.health.status == "CRITICAL"  # 1 disaster problem active on DEV-LEGACY-HOST
        assert validated.health.reason == "active_disaster_problems"
        assert len(validated.health.evidence) > 0

        # Host counts
        assert validated.hosts.total == 5
        assert validated.hosts.available == 3
        assert validated.hosts.unavailable == 1
        assert validated.hosts.maintenance == 1
        assert validated.hosts.unknown == 0

        # Problems severity counts
        assert validated.problems.total == 3
        assert validated.problems.disaster == 1
        assert validated.problems.high == 1
        assert validated.problems.average == 0
        assert validated.problems.warning == 1
        assert validated.problems.information == 0

        # Availability calculation
        assert validated.availability.percent == 80.0  # (3 UP + 1 MAINT) / 5 = 80.0%
        assert "calculation" in validated.availability.lineage

        # Active problems details
        assert len(validated.active_problems) == 3
        first_prob = validated.active_problems[0]
        assert first_prob.severity == 5
        assert first_prob.severity_name == "Disaster"
        assert "DEV-LEGACY-HOST" in first_prob.host_name

        # Top problem hosts
        assert len(validated.top_problem_hosts) == 3
        assert validated.top_problem_hosts[0].highest_severity == 5

        # Recent events
        assert len(validated.recent_events) >= 5

        # Infrastructure categories
        assert any(cat.category == "Linux Servers" for cat in validated.infrastructure)
        assert any(cat.category == "Network Devices" for cat in validated.infrastructure)
        # Unmonitored category explicitly marked NO_DATA
        cloud_cat = next((c for c in validated.infrastructure if "Cloud" in c.category), None)
        assert cloud_cat is not None
        assert cloud_cat.status == "NO_DATA"
        assert cloud_cat.has_telemetry is False


@pytest.mark.asyncio
async def test_overview_filter_by_group():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/overview?group=Linux%20Servers")
        assert response.status_code == 200
        data = response.json()
        validated = OverviewResponseDTO(**data)
        # Only SERVER-APP-01
        assert validated.hosts.total == 1
        assert validated.hosts.available == 1


@pytest.mark.asyncio
async def test_overview_filter_by_severity():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/overview?severity=5")
        assert response.status_code == 200
        data = response.json()
        validated = OverviewResponseDTO(**data)
        # Only disaster problems
        assert validated.problems.total == 1
        assert validated.problems.disaster == 1
        assert validated.problems.high == 0


@pytest.mark.asyncio
async def test_overview_filter_empty_result():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/overview?host=non_existent_host_xyz")
        assert response.status_code == 200
        data = response.json()
        validated = OverviewResponseDTO(**data)
        assert validated.hosts.total == 0
        assert validated.problems.total == 0
        assert validated.availability.percent is None  # Never fake 100% or 0 when no data


@pytest.mark.asyncio
async def test_overview_invalid_query_parameters():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid time range
        resp1 = await client.get("/api/v1/overview?time_range=invalid_range")
        assert resp1.status_code == 422

        # Invalid severity (> 5)
        resp2 = await client.get("/api/v1/overview?severity=99")
        assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_overview_permission_denied():
    from app.core.auth import set_auth_provider, LocalDevAuthProvider
    # Swap auth provider to restricted user
    set_auth_provider(RestrictedMockAuthProvider())
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/overview")
            assert resp.status_code == 403
            assert "Permission denied" in resp.json()["detail"]
    finally:
        # Reset back to local dev admin
        set_auth_provider(LocalDevAuthProvider())


def test_overview_service_directly():
    adapter = MockZabbixAdapter()
    service = OverviewService(adapter=adapter)
    import asyncio
    res = asyncio.run(service.get_overview(OverviewFilterParams(time_range="1h")))
    assert isinstance(res, OverviewResponseDTO)
    assert res.time_range.range_code == "1h"
    assert res.trend.direction in ("improving", "stable", "degrading")
