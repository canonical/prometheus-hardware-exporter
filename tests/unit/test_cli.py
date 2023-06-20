from unittest.mock import Mock, patch

import pytest

from prometheus_hardware_exporter import __main__
from prometheus_hardware_exporter.__main__ import main, parse_command_line
from prometheus_hardware_exporter.config import Config


class TestCli:
    """Cli test class."""

    @patch("argparse.ArgumentParser")
    def test_parse_argument(self, mock_argument_parser):
        parse_command_line()
        mock_argument_parser.assert_called_once()

    @patch.object(__main__, "parse_command_line")
    @patch.object(__main__, "Exporter")
    @patch.object(__main__, "Config")
    @patch("logging.getLevelName")
    def test_cli_main(
        self,
        mock_get_level_name,
        mock_config,
        mock_exporter,
        mock_main_parse_command_line,
    ):
        """Test main function in cli."""
        mock_main_parse_command_line.return_value = Mock()
        mock_get_level_name.return_value = "DEBUG"
        main()
        mock_main_parse_command_line.assert_called_once()
        mock_config.load_config.assert_called_once()
        mock_exporter.assert_called_once()

    @patch.object(__main__, "parse_command_line")
    @patch.object(__main__, "Exporter")
    @patch.object(__main__, "Config")
    def test_cli_main_with_config(self, mock_config, mock_exporter, mock_main_parse_command_line):
        mock_config.load_config.return_value = Config(
            port=10000,
            level="INFO",
            enable_collectors=["mega-raid-collector"],
        )
        mock_main_parse_command_line.return_value = Mock()
        main()
        mock_main_parse_command_line.assert_called_once()
        mock_exporter.assert_called_once()

    @patch.object(__main__, "parse_command_line")
    @patch.object(__main__, "Exporter")
    @patch.object(__main__, "Config")
    def test_cli_main_with_wrong_config(
        self, mock_config, mock_exporter, mock_main_parse_command_line
    ):
        with pytest.raises(ValueError):
            mock_main_parse_command_line.return_value = Mock()
            mock_config.load_config.return_value = Config(
                port=10000,
                level="INFO",
                enable_collectors=["megaraidcollector"],
            )
            main()
            mock_main_parse_command_line.assert_called_once()
            mock_exporter.assert_called_once()
