import pytest
from modules.reports.backend.routes import router


def test_reports_router_exists():
    assert router is not None
