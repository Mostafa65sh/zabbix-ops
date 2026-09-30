import pytest
from modules.network.backend.routes import router


def test_network_router_exists():
    assert router is not None
