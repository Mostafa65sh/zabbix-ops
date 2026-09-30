import pytest
from modules.host360.backend.routes import router


def test_host360_router_exists():
    assert router is not None
