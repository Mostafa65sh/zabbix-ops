import pytest
from modules.intelligence.backend.routes import router


def test_intelligence_router_exists():
    assert router is not None
