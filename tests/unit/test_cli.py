from unittest.mock import Mock, patch

from prometheus_hardware_exporter import __main__
from prometheus_hardware_exporter.__main__ import main, parse_command_line


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
