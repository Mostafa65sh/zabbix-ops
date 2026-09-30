import pytest
from modules.infra_map.backend.routes import router


def test_infra_map_router_exists():
    assert router is not None
