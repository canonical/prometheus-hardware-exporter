import subprocess
import unittest
from unittest.mock import patch

from prometheus_hardware_exporter import utils
from prometheus_hardware_exporter.utils import Command, Result, get_json_output


class TestCommand(unittest.TestCase):
    """Test Command class."""

    @patch.object(Command, "check_output")
    def test_command_installed(self, mock_check_output):
        mock_check_output.return_value = Result("", None)
        command = Command()
        self.assertTrue(command.installed)

    @patch.object(Command, "check_output")
    def test_command_not_installed(self, mock_check_output):
        mock_check_output.return_value = Result("", Exception())
        command = Command()
        self.assertFalse(command.installed)

    @patch.object(utils.subprocess, "check_output")
    def test_check_output_okay(self, mock_subprocess_check_output):
        mock_subprocess_check_output.return_value = b""
        command = Command()
        command.installed = True
        result = command()
        self.assertEqual(result.data, "")
        self.assertEqual(result.error, None)

    @patch.object(utils.subprocess, "check_output")
    def test_check_output_failed(self, mock_subprocess_check_output):
        mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(1, "cmd")
        command = Command()
        command.installed = True
        result = command()
        self.assertEqual(result.data, "")
        self.assertEqual(str(result.error), "Command 'cmd' returned non-zero exit status 1.")
        self.assertEqual(type(result.error), subprocess.CalledProcessError)


def test_get_json_output():
    result = get_json_output("""{"a": 1, "b": 2}""")
    assert result == {"a": 1, "b": 2}


def test_get_json_output_err():
    result = get_json_output("""{"a": 1, "b": 2}123""")
    assert isinstance(result, Exception)
