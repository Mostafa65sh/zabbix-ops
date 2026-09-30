import pytest
from modules.database.backend.routes import router


def test_database_router_exists():
    assert router is not None
