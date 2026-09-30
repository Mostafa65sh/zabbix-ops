import pytest
from modules.availability.backend.routes import router


def test_availability_router_exists():
    assert router is not None
