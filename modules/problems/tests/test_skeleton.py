import pytest
from modules.problems.backend.routes import router


def test_problems_router_exists():
    assert router is not None
