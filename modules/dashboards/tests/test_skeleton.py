import pytest
from modules.dashboards.backend.routes import router


def test_dashboards_router_exists():
    assert router is not None
