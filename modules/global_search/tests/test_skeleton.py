import pytest
from modules.global_search.backend.routes import router


def test_global_search_router_exists():
    assert router is not None
