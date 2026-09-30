import pytest
from modules.trend_detection.backend.routes import router


def test_trend_detection_router_exists():
    assert router is not None
