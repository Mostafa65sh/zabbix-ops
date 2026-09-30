import pytest
from modules.services.backend.routes import router


def test_services_router_exists():
    assert router is not None
