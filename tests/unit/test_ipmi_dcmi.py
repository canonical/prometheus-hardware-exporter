import unittest
from unittest.mock import patch

from prometheus_hardware_exporter.collectors.ipmi_dcmi import IpmiDcmi, IpmiTool
from prometheus_hardware_exporter.utils import Command, Result

DCMI_SAMPLE_OUTPUT = "tests/unit/test_resources/ipmi/ipmi_dcmi_sample_output.txt"
IPMITOOL_SDR_PS_SAMPLE_OUTPUT = "tests/unit/test_resources/ipmi/ipmitool_sdr_ps_sample_output.txt"


class TestIpmiDcmi(unittest.TestCase):
    """Test the IpmiDcmi class."""

    @patch.object(Command, "__call__")
    def test_00_get_current_power_success(self, mock_call):
        with open(DCMI_SAMPLE_OUTPUT, "r") as content:
            mock_call.return_value = Result(content.read(), None)
            ipmi_dcmi = IpmiDcmi()
            payload = ipmi_dcmi.get_current_power()
            self.assertEqual(payload, {"current_power": 105})

    @patch.object(Command, "__call__")
    def test_01_get_current_power_error(self, mock_call):
        mock_call.return_value = Result("", True)
        ipmi_dcmi = IpmiDcmi()
        payload = ipmi_dcmi.get_current_power()
        self.assertEqual(payload, {})

    @patch.object(Command, "__call__")
    def test_01_get_current_power_parse_failure(self, mock_call):
        mock_call.return_value = Result("", None)
        ipmi_dcmi = IpmiDcmi()
        payload = ipmi_dcmi.get_current_power()
        self.assertEqual(payload, {})


class TestIpmiTool(unittest.TestCase):
    """Test the IpmiTool class."""

    @patch.object(Command, "__call__")
    def test_00_get_ps_redundancy_success(self, mock_call):
        with open(IPMITOOL_SDR_PS_SAMPLE_OUTPUT, "r") as content:
            mock_call.return_value = Result(content.read(), None)
        ipmitool = IpmiTool()
        ps_redundancy = ipmitool.get_ps_redundancy()
        self.assertEqual(ps_redundancy, (True, True))

    @patch.object(Command, "__call__")
    def test_01_get_ps_redundancy_error(self, mock_call):
        mock_call.return_value = Result("", True)
        ipmitool = IpmiTool()
        ps_redundancy = ipmitool.get_ps_redundancy()
        self.assertEqual(ps_redundancy, (False, False))
