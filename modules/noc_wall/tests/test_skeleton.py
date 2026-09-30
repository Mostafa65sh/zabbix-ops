import pytest
from modules.noc_wall.backend.routes import router


def test_noc_wall_router_exists():
    assert router is not None
