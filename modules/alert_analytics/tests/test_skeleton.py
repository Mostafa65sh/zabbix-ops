import pytest
from modules.alert_analytics.backend.routes import router


def test_alert_analytics_router_exists():
    assert router is not None
