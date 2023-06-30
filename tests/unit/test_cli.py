from unittest.mock import patch

from prometheus_hardware_exporter import __main__
from prometheus_hardware_exporter.__main__ import main, parse_command_line
from prometheus_hardware_exporter.config import Config


class TestCli:
    """Cli test class."""

    @patch("argparse.ArgumentParser")
    def test_parse_argument(self, mock_argument_parser):
        parse_command_line()
        mock_argument_parser.assert_called_once()

    @patch.object(__main__, "Exporter")
    def test_cli_main(self, mock_exporter):
        mock_port = 10000
        mock_level = "INFO"
        mock_enable_collectors = ["collector.mega_raid"]
        config = Config(port=mock_port, level=mock_level, enable_collectors=mock_enable_collectors)
        main(config)
        mock_exporter.assert_called_once_with(mock_port)
