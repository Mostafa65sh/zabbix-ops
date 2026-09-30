import pytest
from modules.graph_explorer.backend.routes import router


def test_graph_explorer_router_exists():
    assert router is not None
