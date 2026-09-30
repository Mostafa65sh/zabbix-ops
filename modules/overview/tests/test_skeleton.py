import pytest
from modules.overview.backend.routes import router


def test_overview_router_exists():
    assert router is not None
