import unittest
from unittest.mock import patch

from prometheus_hardware_exporter.utils import Command


class TestCommand(unittest.TestCase):
    """Test Command class."""

    @patch.object(Command, "check_output")
    def test_check_installed(self, mock_check_output):
        mock_check_output.return_value = True, False
        command = Command()
        self.assertTrue(command.check_installed())

    @patch.object(Command, "check_installed")
    @patch.object(Command, "check_output")
    def test_call_okay(self, mock_check_output, mock_check_installed):
        mock_check_installed.return_value = True, False
        mock_check_output.return_value = True, False
        command = Command()
        result, error = command()
        self.assertFalse(error)

    @patch.object(Command, "check_installed")
    @patch.object(Command, "check_output")
    def test_call_failed(self, mock_check_output, mock_check_installed):
        mock_check_installed.return_value = True, False
        mock_check_output.return_value = False, True
        command = Command()
        result, error = command()
        print(result, error)
        self.assertTrue(error)
        self.assertIsNone(result)
