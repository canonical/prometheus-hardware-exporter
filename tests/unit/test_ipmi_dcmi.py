import unittest
from unittest.mock import patch

from prometheus_hardware_exporter.collectors.ipmi_dcmi import IpmiDcmi, IpmiTool
from prometheus_hardware_exporter.config import Config
from prometheus_hardware_exporter.utils import Command, Result

DCMI_SAMPLE_OUTPUT = "tests/unit/test_resources/ipmi/ipmi_dcmi_sample_output.txt"
IPMITOOL_SDR_PS_SAMPLE_OUTPUT = "tests/unit/test_resources/ipmi/ipmitool_sdr_ps_sample_output.txt"


IPMITOOL_LAN_PRINT_SAMPLE_OUTPUT = (
    "IP Address Source       : DHCP Address\n"
    "IP Address              : 0.0.0.0\n"
    "Subnet Mask             : 255.255.255.0\n"
    "MAC Address             : 00:00:00:00:00:00\n"
    "SNMP Community String   : public\n"
)


class TestIpmiDcmi(unittest.TestCase):
    """Test the IpmiDcmi class."""

    @patch.object(Command, "__call__")
    def test_00_get_current_power_success(self, mock_call):
        with open(DCMI_SAMPLE_OUTPUT, "r") as content:
            mock_call.return_value = Result(content.read(), None)
            config = Config()
            ipmi_dcmi = IpmiDcmi(config)
            payload = ipmi_dcmi.get_current_power()
            self.assertEqual(payload, {"current_power": 105})

    @patch.object(Command, "__call__")
    def test_01_get_current_power_error(self, mock_call):
        mock_call.return_value = Result("", True)
        config = Config()
        ipmi_dcmi = IpmiDcmi(config)
        payload = ipmi_dcmi.get_current_power()
        self.assertEqual(payload, {})

    @patch.object(Command, "__call__")
    def test_01_get_current_power_parse_failure(self, mock_call):
        mock_call.return_value = Result("", None)
        config = Config()
        ipmi_dcmi = IpmiDcmi(config)
        payload = ipmi_dcmi.get_current_power()
        self.assertEqual(payload, {})


class TestIpmiTool(unittest.TestCase):
    """Test the IpmiTool class."""

    @patch.object(Command, "__call__")
    def test_00_get_ps_redundancy_success(self, mock_call):
        with open(IPMITOOL_SDR_PS_SAMPLE_OUTPUT, "r") as content:
            mock_call.return_value = Result(content.read(), None)
        config = Config()
        ipmitool = IpmiTool(config)
        ps_redundancy = ipmitool.get_ps_redundancy()
        self.assertEqual(ps_redundancy, (True, True))

    @patch.object(Command, "__call__")
    def test_01_get_ps_redundancy_error(self, mock_call):
        mock_call.return_value = Result("", True)
        config = Config()
        ipmitool = IpmiTool(config)
        ps_redundancy = ipmitool.get_ps_redundancy()
        self.assertEqual(ps_redundancy, (False, False))

    @patch.object(Command, "__call__")
    def test_02_get_ps_redundancy_success_redundancy_disable(self, mock_call):
        with open(IPMITOOL_SDR_PS_SAMPLE_OUTPUT, "r") as content:
            data = content.read().replace("Fully Redundant", "Not Fully Redundant")
            mock_call.return_value = Result(data, None)
        config = Config()
        ipmitool = IpmiTool(config)
        ps_redundancy = ipmitool.get_ps_redundancy()
        self.assertEqual(ps_redundancy, (True, False))

    @patch.object(Command, "__call__")
    def test_03_get_ipmi_host_success(self, mock_call):
        mock_call.return_value = Result(IPMITOOL_LAN_PRINT_SAMPLE_OUTPUT, None)
        config = Config()
        ipmitool = IpmiTool(config)
        ipmi_host = ipmitool.get_ipmi_host()
        self.assertEqual(ipmi_host, "0.0.0.0")

    @patch.object(Command, "__call__")
    def test_04_get_ipmi_host_error(self, mock_call):
        mock_call.return_value = Result("", True)
        config = Config()
        ipmitool = IpmiTool(config)
        ipmi_host = ipmitool.get_ipmi_host()
        self.assertEqual(ipmi_host, None)

    @patch.object(Command, "__call__")
    def test_04_get_ipmi_no_host(self, mock_call):
        mock_call.return_value = Result("", None)
        config = Config()
        ipmitool = IpmiTool(config)
        ipmi_host = ipmitool.get_ipmi_host()
        self.assertEqual(ipmi_host, None)
