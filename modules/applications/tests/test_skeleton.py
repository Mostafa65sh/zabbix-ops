import pytest
from modules.applications.backend.routes import router


def test_applications_router_exists():
    assert router is not None
