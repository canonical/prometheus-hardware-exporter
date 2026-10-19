from unittest.mock import Mock, patch

import pytest

from prometheus_hardware_exporter import exporter
from prometheus_hardware_exporter.exporter import Exporter


class TestExporter:
    """Exporter test class."""

    @patch.object(exporter, "threading")
    @patch.object(exporter, "REGISTRY")
    @patch.object(exporter, "make_server")
    def test_exporter(self, mock_make_server, mock_registry, mock_threading):
        exporter = Exporter(10000)
        exporter.register(Mock())
        exporter.run(daemon=True)

        mock_make_server.assert_called_once()
        mock_registry.register.assert_called_once()
        mock_threading.Thread.assert_called_once()


@pytest.mark.parametrize("address", ["127.0.0.1", "0.0.0.0"])
def test_server_bind_address(address):
    instance = Exporter(10000) if address == "127.0.0.1" else Exporter(10000, addr=address)
    with patch.object(exporter, "make_server") as server:
        with patch.object(exporter, "threading"):
            instance.run()
    assert server.call_args.args[:2] == (address, 10000)
