import unittest
from unittest.mock import patch

from test_resources.ssacli.sample_outputs import (
    CTRL_ALL_SHOW,
    CTRL_LD_ALL_SHOW_STATUS,
    CTRL_LD_ALL_SHOW_STATUS_ABSENT,
    CTRL_PD_ALL_SHOW_STATUS,
    CTRL_PD_ALL_SHOW_STATUS_ABSENT,
    CTRL_SHOW_STATUS,
)

from prometheus_hardware_exporter.collectors.ssacli import SsaCLI
from prometheus_hardware_exporter.utils import Command, Result


class TestSsaCLI(unittest.TestCase):
    """Test the SsaCLI class."""

    @patch.object(Command, "__call__")
    def test_00__get_controller_slots_success(self, mock_call):
        mock_call.return_value = Result(CTRL_ALL_SHOW, None)
        ssacli = SsaCLI()
        slots = ssacli._get_controller_slots()
        self.assertEqual(slots, ["2", "3"])

    @patch.object(Command, "__call__")
    def test_01__get_controller_slots_error(self, mock_call):
        mock_call.return_value = Result("", True)
        ssacli = SsaCLI()
        slots = ssacli._get_controller_slots()
        self.assertEqual(slots, [])

    @patch.object(Command, "__call__")
    def test_10__get_controller_status_success(self, mock_call):
        mock_call.return_value = Result(CTRL_SHOW_STATUS, None)
        ssacli = SsaCLI()
        ctrl_status = ssacli._get_controller_status(1)
        expected_ctrl_status = {
            "Controller Status": "OK",
            "Cache Status": "OK",
            "Battery/Capacitor Status": "OK",
        }
        self.assertEqual(ctrl_status, expected_ctrl_status)

    @patch.object(Command, "__call__")
    def test_11__get_controller_status_error(self, mock_call):
        mock_call.return_value = Result("", True)
        ssacli = SsaCLI()
        ctrl_status = ssacli._get_controller_status(1)
        self.assertEqual(ctrl_status, {})

    @patch.object(Command, "__call__")
    def test_20__get_ld_status_success(self, mock_call):
        mock_call.return_value = Result(CTRL_LD_ALL_SHOW_STATUS, None)
        ssacli = SsaCLI()
        ld_status = ssacli._get_ld_status(1)
        expected_ld_status = {"1": "OK"}
        self.assertEqual(ld_status, expected_ld_status)

    @patch.object(Command, "__call__")
    def test_21__get_ld_status_error(self, mock_call):
        mock_call.return_value = Result("", True)
        ssacli = SsaCLI()
        ld_status = ssacli._get_ld_status(1)
        self.assertEqual(ld_status, {})

    @patch.object(Command, "__call__")
    def test_22__get_ld_status_absent(self, mock_call):
        mock_call.return_value = Result(CTRL_LD_ALL_SHOW_STATUS_ABSENT, None)
        ssacli = SsaCLI()
        ld_status = ssacli._get_ld_status(1)
        self.assertEqual(ld_status, {})

    @patch.object(Command, "__call__")
    def test_30__get_pd_status_success(self, mock_call):
        mock_call.return_value = Result(CTRL_PD_ALL_SHOW_STATUS, None)
        ssacli = SsaCLI()
        pd_status = ssacli._get_pd_status(1)
        expected_pd_status = {"2I:0:1": "OK", "2I:0:2": "OK"}
        self.assertEqual(pd_status, expected_pd_status)

    @patch.object(Command, "__call__")
    def test_31__get_pd_status_error(self, mock_call):
        mock_call.return_value = Result("", True)
        ssacli = SsaCLI()
        pd_status = ssacli._get_pd_status(1)
        self.assertEqual(pd_status, {})

    @patch.object(Command, "__call__")
    def test_32__get_pd_status_absent(self, mock_call):
        mock_call.return_value = Result(CTRL_PD_ALL_SHOW_STATUS_ABSENT, None)
        ssacli = SsaCLI()
        pd_status = ssacli._get_pd_status(1)
        self.assertEqual(pd_status, {})

    @patch.object(SsaCLI, "_get_controller_slots")
    @patch.object(SsaCLI, "_get_controller_status")
    @patch.object(SsaCLI, "_get_ld_status")
    @patch.object(SsaCLI, "_get_pd_status")
    def test_40_get_payload(
        self, mock_pd_status, mock_ld_status, mock_controller_status, mock_controller_slots
    ):
        mock_controller_slots.return_value = ["1"]
        mock_controller_status.return_value = {
            "Controller Status": " OK",
            "Cache Status": " OK",
            "Battery/Capacitor Status": " OK",
        }
        mock_ld_status.return_value = {"1": "OK"}
        mock_pd_status.return_value = {"2I:0:1": "OK", "2I:0:2": "OK"}
        ssacli = SsaCLI()
        payload = ssacli.get_payload()
        expected_payload = {
            "1": {
                "controller_status": {
                    "Controller Status": " OK",
                    "Cache Status": " OK",
                    "Battery/Capacitor Status": " OK",
                },
                "ld_status": {"1": "OK"},
                "pd_status": {"2I:0:1": "OK", "2I:0:2": "OK"},
            }
        }
        self.assertEqual(payload, expected_payload)
