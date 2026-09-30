import pytest
from modules.top_n.backend.routes import router


def test_top_n_router_exists():
    assert router is not None
