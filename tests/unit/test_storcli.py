import unittest
from unittest.mock import patch

from prometheus_hardware_exporter.collectors.storcli import StorCLI
from prometheus_hardware_exporter.utils import Command

SHOW_CTRLCOUNT = "tests/unit/test_resources/show_ctrlcount.txt"
SHOW_ALL = "tests/unit/test_resources/show_all.txt"
CX_VALL_SHOW_ALL = "tests/unit/test_resources/cx_vall_show_all.txt"


class TestStorCLI(unittest.TestCase):
    """Test StorCLI class."""

    @patch.object(Command, "__call__")
    def test_00_get_controllers_okay(self, mock_call):
        with open(SHOW_ALL, "r") as content:
            mock_call.return_value = content.read(), False
            storcli = StorCLI()
            payload, _ = storcli.get_controllers()
            self.assertEqual(payload, {"count": 1, "hostname": "kongfu"})

    @patch.object(Command, "__call__")
    def test_01_get_controllers_failed(self, mock_call):
        mock_call.return_value = "", False
        storcli = StorCLI()
        payload, _ = storcli.get_controllers()
        self.assertIsNone(payload)

    @patch.object(StorCLI, "_get_controller_ids")
    @patch.object(Command, "__call__")
    def test_10_get_all_virtual_drives_okay(self, mock_call, mock__get_controller_ids):
        with open(CX_VALL_SHOW_ALL, "r") as content:
            mock_call.return_value = content.read(), False
            mock__get_controller_ids.return_value = [1], False
            storcli = StorCLI()
            payload, _ = storcli.get_all_virtual_drives()
            self.assertEqual(
                payload, {1: [{"DG": "0", "VD": "239", "state": "Optl", "cache": "NRWTD"}]}
            )

    @patch.object(StorCLI, "_get_all_virtual_drives")
    @patch.object(StorCLI, "_get_controller_ids")
    @patch.object(Command, "__call__")
    def test_11_get_all_virtual_drives_failed(
        self, mock_call, mock__get_controller_ids, mock__get_all_virtual_drives
    ):
        with open(CX_VALL_SHOW_ALL, "r") as content:
            mock_call.return_value = content.read(), False
            mock__get_controller_ids.return_value = [1], False
            mock__get_all_virtual_drives.return_value = None, True
            storcli = StorCLI()
            payload, _ = storcli.get_all_virtual_drives()
            self.assertIsNone(payload)

    @patch.object(Command, "__call__")
    def test_20__get_controller_id_okay(self, mock_call):
        with open(SHOW_CTRLCOUNT, "r") as content:
            mock_call.return_value = content.read(), False
            storcli = StorCLI()
            payload, _ = storcli._get_controller_ids()
            self.assertEqual(payload, [0])

    @patch.object(Command, "__call__")
    def test_21__get_controller_id_failed(self, mock_call):
        mock_call.return_value = "", False
        storcli = StorCLI()
        payload, _ = storcli._get_controller_ids()
        self.assertIsNone(payload)

    @patch.object(Command, "__call__")
    def test_30__get_all_virtual_drives_failed(self, mock_call):
        mock_call.return_value = "", False
        storcli = StorCLI()
        payload, _ = storcli._get_all_virtual_drives(0)
        self.assertIsNone(payload)

    @patch.object(Command, "__call__")
    def test_31__get_all_virtual_drives_failed(self, mock_call):
        mock_call.return_value = "", True
        storcli = StorCLI()
        payload, _ = storcli._get_all_virtual_drives(0)
        self.assertIsNone(payload)
