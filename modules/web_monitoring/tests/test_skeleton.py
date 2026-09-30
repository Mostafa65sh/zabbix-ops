import pytest
from modules.web_monitoring.backend.routes import router


def test_web_monitoring_router_exists():
    assert router is not None
