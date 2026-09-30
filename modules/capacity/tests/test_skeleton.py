import pytest
from modules.capacity.backend.routes import router


def test_capacity_router_exists():
    assert router is not None
