import subprocess
import unittest
from unittest.mock import patch

from prometheus_hardware_exporter import utils
from prometheus_hardware_exporter.config import Config
from prometheus_hardware_exporter.utils import Command, Result, get_json_output


class TestCommand(unittest.TestCase):
    """Test Command class."""

    @patch.object(Command, "check_output")
    def test_command_installed(self, mock_check_output):
        mock_check_output.return_value = Result("", None)
        config = Config()
        command = Command(config)
        result = command(config)
        self.assertTrue(command.installed)
        self.assertEqual(result.error, None)

    @patch.object(Command, "check_output")
    def test_command_not_installed(self, mock_check_output):
        mock_check_output.return_value = Result("", Exception())
        config = Config()
        command = Command(config)
        result = command()
        self.assertFalse(command.installed)
        self.assertEqual(type(result.error), ValueError)

    @patch.object(utils.subprocess, "check_output")
    def test_check_output_okay(self, mock_subprocess_check_output):
        mock_subprocess_check_output.return_value = b""
        config = Config()
        command = Command(config)
        command.installed = True
        result = command()
        self.assertEqual(result.data, "")
        self.assertEqual(result.error, None)

    @patch.object(utils.subprocess, "check_output")
    def test_check_output_failed(self, mock_subprocess_check_output):
        mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(1, "cmd")
        config = Config()
        command = Command(config)
        command.installed = True
        result = command()
        self.assertEqual(result.data, "")
        self.assertEqual(str(result.error), "Command 'cmd' returned non-zero exit status 1.")
        self.assertEqual(type(result.error), subprocess.CalledProcessError)

    @patch.object(utils.subprocess, "check_output")
    def test_check_output_timeout(self, mock_subprocess_check_output):
        config = Config()
        command = Command(config)
        command.installed = True
        command()

        # We don't actually test the timeout but make sure the timeout argument
        # is been passed to subprocess
        mock_subprocess_check_output.assert_called_with("", shell=True, timeout=30)


def test_get_json_output():
    result = get_json_output("""{"a": 1, "b": 2}""")
    assert result == {"a": 1, "b": 2}


def test_get_json_output_err():
    result = get_json_output("""{"a": 1, "b": 2}123""")
    assert isinstance(result, Exception)
