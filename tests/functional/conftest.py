import pytest

from prometheus_hardware_exporter.__main__ import main


@pytest.fixture(scope="session")
def port():
    return 10000


@pytest.fixture(scope="session")
def level():
    return "INFO"


@pytest.fixture(scope="session")
def enable_collectors():
    return []


@pytest.fixture(scope="session", autouse=True)
def exporter(port, level, enable_collectors):
    """Start the exporter service as a daemon service."""
    return main(port, level, enable_collectors, daemon=True)
