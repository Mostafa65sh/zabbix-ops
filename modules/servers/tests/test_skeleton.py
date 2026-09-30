import pytest
from modules.servers.backend.routes import router


def test_servers_router_exists():
    assert router is not None
