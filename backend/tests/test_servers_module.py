import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from modules.servers.backend.schemas import (
    ServerListResponseDTO,
    ServerDetailResponseDTO,
    ServerFilterParams
)
from modules.servers.backend.services import ServersService
from app.adapters.zabbix.mock import MockZabbixAdapter
from app.adapters.zabbix.base import ZabbixAdapterBase
from app.core.auth import User, set_auth_provider, LocalDevAuthProvider, BaseAuthProvider


class RestrictedServersAuthProvider(BaseAuthProvider):
    async def authenticate(self, credentials: dict):
        return None

    async def get_user_by_id(self, user_id: str):
        # User without module.servers.view permission
        return User(
            id="usr_restricted_servers",
            username="restricted_servers_user",
            is_superuser=False,
            roles=["viewer"],
            permissions=["module.overview.view"]  # Has overview, but NOT servers
        )


class FailingZabbixAdapter(MockZabbixAdapter):
    async def get_server_inventory(self, *args, **kwargs):
        raise RuntimeError("Zabbix JSON-RPC Gateway Timeout")


class LargeScaleZabbixAdapter(MockZabbixAdapter):
    async def get_server_inventory(self, *args, **kwargs):
        base_servers = await super().get_server_inventory()
        # Replicate to create 120 hosts
        large_list = []
        for i in range(12):
            for s in base_servers:
                clone = dict(s)
                clone["hostid"] = f"{s['hostid']}_{i}"
                clone["name"] = f"{s['name']}-NODE-{i:02d}"
                large_list.append(clone)
        return large_list


# 1. Server list rendering / endpoint response
@pytest.mark.asyncio
async def test_server_list_rendering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/servers")
        assert resp.status_code == 200
        data = resp.json()

        validated = ServerListResponseDTO(**data)
        assert validated.total_count == 10
        assert len(validated.items) == 10
        assert validated.page == 1
        assert validated.total_pages == 1

        # Summary KPIs
        assert validated.summary.total_servers == 10
        assert validated.summary.servers_up == 8
        assert validated.summary.servers_down == 1
        assert validated.summary.servers_maintenance == 1
        assert validated.summary.available_count == 9
        assert validated.summary.unavailable_count == 1
        assert validated.summary.avg_cpu_percent is not None
        assert validated.summary.avg_memory_percent is not None
        assert validated.summary.avg_storage_percent is not None

        # Verify first item structure
        first = validated.items[0]
        assert first.id != ""
        assert first.name != ""
        assert first.ip != ""
        assert first.status in ("UP", "DOWN", "MAINTENANCE")
        assert first.overall_availability in ("AVAILABLE", "UNAVAILABLE", "UNKNOWN")
        assert "host" in first.data_lineage


# 2. API/service layer direct test
@pytest.mark.asyncio
async def test_server_service_layer_direct():
    adapter = MockZabbixAdapter()
    service = ServersService(adapter=adapter)

    res = await service.get_servers(ServerFilterParams(search="APP-01"))
    assert res.total_count == 1
    server = res.items[0]
    assert server.name == "SERVER-APP-01"
    assert server.hardware.cpu_utilization.value == 28.5
    assert server.hardware.cpu_utilization.status == "NORMAL"
    assert server.hardware.memory_utilization.value == 64.2
    assert server.hardware.storage_utilization.value == 86.4
    assert server.hardware.storage_utilization.status == "WARNING"  # >= 70%
    assert server.datacenter == "DC-EAST-01"
    assert server.rack == "RACK-A4"


# 3. Empty result handling
@pytest.mark.asyncio
async def test_server_empty_result():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/servers?search=non_existent_server_xyz123")
        assert resp.status_code == 200
        data = resp.json()
        validated = ServerListResponseDTO(**data)
        assert validated.total_count == 0
        assert len(validated.items) == 0
        assert validated.total_pages == 1
        # Never fake averages when no data exists!
        assert validated.summary.avg_cpu_percent is None
        assert validated.summary.avg_memory_percent is None
        assert validated.summary.avg_storage_percent is None


# 4. API failure / exception handling
@pytest.mark.asyncio
async def test_server_api_failure_handling():
    failing_adapter = FailingZabbixAdapter()
    service = ServersService(adapter=failing_adapter)
    with pytest.raises(RuntimeError) as exc_info:
        await service.get_servers(ServerFilterParams())
    assert "Zabbix JSON-RPC Gateway Timeout" in str(exc_info.value)


# 5. Permission denial
@pytest.mark.asyncio
async def test_server_permission_denial():
    set_auth_provider(RestrictedServersAuthProvider())
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/servers")
            assert resp.status_code == 403
            assert "Permission denied" in resp.json()["detail"]

            # Also verify detail endpoint is protected
            detail_resp = await client.get("/api/v1/servers/10001")
            assert detail_resp.status_code == 403
    finally:
        set_auth_provider(LocalDevAuthProvider())


# 6. Filtering (group, status, availability, os_type, datacenter, problems, severity)
@pytest.mark.asyncio
async def test_server_filtering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Group filter
        resp_grp = await client.get("/api/v1/servers?group=Windows%20Servers")
        assert resp_grp.status_code == 200
        data_grp = resp_grp.json()
        assert data_grp["total_count"] == 1
        assert data_grp["items"][0]["name"] == "SERVER-WIN-AD01"

        # Status filter
        resp_stat = await client.get("/api/v1/servers?status=DOWN")
        assert resp_stat.status_code == 200
        data_stat = resp_stat.json()
        assert data_stat["total_count"] == 1
        assert data_stat["items"][0]["name"] == "DEV-LEGACY-HOST"

        # OS type filter
        resp_os = await client.get("/api/v1/servers?os_type=windows")
        assert resp_os.status_code == 200
        assert resp_os.json()["total_count"] == 1

        # Datacenter filter
        resp_dc = await client.get("/api/v1/servers?datacenter=DC-WEST-02")
        assert resp_dc.status_code == 200
        assert resp_dc.json()["total_count"] == 1
        assert resp_dc.json()["items"][0]["name"] == "BACKUP-STORAGE-02"

        # Has problems filter
        resp_prob = await client.get("/api/v1/servers?has_problems=true")
        assert resp_prob.status_code == 200
        assert resp_prob.json()["total_count"] >= 3

        # Minimum severity filter (severity=5 Disaster)
        resp_sev = await client.get("/api/v1/servers?severity=5")
        assert resp_sev.status_code == 200
        assert resp_sev.json()["total_count"] == 1
        assert resp_sev.json()["items"][0]["name"] == "DEV-LEGACY-HOST"


# 7. Pagination and Sorting
@pytest.mark.asyncio
async def test_server_pagination_and_sorting():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Page 1 of size 3
        resp_p1 = await client.get("/api/v1/servers?page=1&page_size=3")
        assert resp_p1.status_code == 200
        d1 = resp_p1.json()
        assert len(d1["items"]) == 3
        assert d1["total_count"] == 10
        assert d1["total_pages"] == 4
        assert d1["page"] == 1

        # Page 2 of size 3
        resp_p2 = await client.get("/api/v1/servers?page=2&page_size=3")
        assert resp_p2.status_code == 200
        d2 = resp_p2.json()
        assert len(d2["items"]) == 3
        assert d2["page"] == 2

        # Verify no overlap between page 1 and page 2
        p1_ids = {x["id"] for x in d1["items"]}
        p2_ids = {x["id"] for x in d2["items"]}
        assert p1_ids.isdisjoint(p2_ids)

        # Sort by cpu descending
        resp_cpu = await client.get("/api/v1/servers?sort_by=cpu&sort_order=desc")
        assert resp_cpu.status_code == 200
        items_cpu = resp_cpu.json()["items"]
        # Highest CPU is SERVER-K8S-WORKER-01 (72.8%)
        assert items_cpu[0]["name"] == "SERVER-K8S-WORKER-01"
        assert items_cpu[0]["hardware"]["cpu_utilization"]["value"] == 72.8


# 8. Availability and status mapping
@pytest.mark.asyncio
async def test_server_availability_and_status_mapping():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/servers")
        items = resp.json()["items"]

        # UP host with agent available
        up_host = next(x for x in items if x["name"] == "SERVER-APP-01")
        assert up_host["status"] == "UP"
        assert up_host["overall_availability"] == "AVAILABLE"
        assert up_host["interfaces"][0]["type"] == "AGENT"
        assert up_host["interfaces"][0]["availability"] == "AVAILABLE"

        # DOWN host with agent unavailable
        down_host = next(x for x in items if x["name"] == "DEV-LEGACY-HOST")
        assert down_host["status"] == "DOWN"
        assert down_host["overall_availability"] == "UNAVAILABLE"
        assert down_host["interfaces"][0]["availability"] == "UNAVAILABLE"
        assert "Connection refused" in down_host["interfaces"][0]["error"]

        # Network host with SNMP
        net_host = next(x for x in items if x["name"] == "BORDER-GATEWAY-01")
        assert net_host["interfaces"][0]["type"] == "SNMP"
        assert net_host["interfaces"][0]["availability"] == "AVAILABLE"


# 9. Invalid/missing host data (Golden Rule: never fake telemetry)
@pytest.mark.asyncio
async def test_server_missing_data_golden_rule():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/servers?search=DEV-LEGACY-HOST")
        assert resp.status_code == 200
        host = resp.json()["items"][0]

        # Missing metrics MUST have value None and status "NO_DATA"
        assert host["hardware"]["cpu_utilization"]["value"] is None
        assert host["hardware"]["cpu_utilization"]["status"] == "NO_DATA"
        assert host["hardware"]["cpu_utilization"]["formatted"] == "NO_DATA"

        assert host["hardware"]["memory_utilization"]["value"] is None
        assert host["hardware"]["memory_utilization"]["status"] == "NO_DATA"

        assert host["hardware"]["storage_utilization"]["value"] is None
        assert host["hardware"]["storage_utilization"]["status"] == "NO_DATA"


# 10. Large-result handling and boundary conditions
@pytest.mark.asyncio
async def test_server_large_result_handling():
    adapter = LargeScaleZabbixAdapter()
    service = ServersService(adapter=adapter)

    # Query with default page size
    res1 = await service.get_servers(ServerFilterParams(page=1, page_size=25))
    assert res1.total_count == 120
    assert len(res1.items) == 25
    assert res1.total_pages == 5

    # Query last page
    res_last = await service.get_servers(ServerFilterParams(page=5, page_size=25))
    assert len(res_last.items) == 20
    assert res_last.page == 5

    # Page clamp if out of bounds
    res_clamp = await service.get_servers(ServerFilterParams(page=999, page_size=25))
    assert res_clamp.page == 5


# 11. Server detail endpoint
@pytest.mark.asyncio
async def test_server_detail_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Valid host
        resp = await client.get("/api/v1/servers/10001")
        assert resp.status_code == 200
        detail = ServerDetailResponseDTO(**resp.json())
        assert detail.server.id == "10001"
        assert detail.server.name == "SERVER-APP-01"
        assert "Dell PowerEdge" in detail.inventory["hardware"]
        assert len(detail.server.interfaces) == 1
        assert "cpu" in detail.metrics_breakdown

        # Non-existent host (404)
        resp_404 = await client.get("/api/v1/servers/non_existent_9999")
        assert resp_404.status_code == 404
        assert "was not found" in resp_404.json()["detail"]
