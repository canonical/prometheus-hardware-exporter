from unittest.mock import Mock, patch

from prometheus_hardware_exporter import __main__
from prometheus_hardware_exporter.__main__ import (
    main,
    parse_command_line,
    start_exporter,
)
from prometheus_hardware_exporter.config import Config


class TestCli:
    """Cli test class."""

    @patch("argparse.ArgumentParser")
    def test_parse_argument(self, mock_argument_parser):
        parse_command_line()
        mock_argument_parser.assert_called_once()

    @patch.object(__main__, "Config")
    @patch.object(__main__, "start_exporter")
    @patch.object(__main__, "parse_command_line")
    def test_cli_main_with_config_file(self, mock_parse_cli, mock_start_exporter, mock_config):
        mock_ns = Mock()
        mock_ns.config = Mock()
        mock_parse_cli.return_value = mock_ns
        mock_config.load_config.return_value = Mock()
        main()
        mock_config.load_config.assert_called_once_with(config_file=mock_ns.config)

    @patch.object(__main__, "Config")
    @patch.object(__main__, "start_exporter")
    @patch.object(__main__, "parse_command_line")
    def test_cli_main_with_arguments(self, mock_parse_cli, mock_start_exporter, mock_config):
        mock_ns = Mock()
        mock_ns.config = False
        mock_ns.collector_redfish = True
        mock_parse_cli.return_value = mock_ns
        mock_config.load_config.return_value = Mock()
        main()
        mock_config.assert_called_once()

    @patch.object(__main__, "Exporter")
    def test_start_exporter(self, mock_exporter):
        mock_port = 10000
        mock_level = "INFO"
        mock_enable_collectors = ["collector.mega_raid"]
        config = Config(port=mock_port, level=mock_level, enable_collectors=mock_enable_collectors)
        start_exporter(config)
        mock_exporter.assert_called_once_with(mock_port)
