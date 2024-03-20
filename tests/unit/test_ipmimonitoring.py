import unittest
from unittest.mock import patch

from prometheus_hardware_exporter.collectors.ipmimonitoring import IpmiMonitoring
from prometheus_hardware_exporter.config import Config
from prometheus_hardware_exporter.utils import Command, Result

IPMIMONITORING_SAMPLE_OUTPUT = "tests/unit/test_resources/ipmi/ipmimonitoring_sample_output.txt"
SAMPLE_SENSOR_ENTRIES = [
    {
        "ID": "0",
        "Name": "UID",
        "Type": "OEM Reserved",
        "State": "N/A",
        "Reading": "N/A",
        "Units": "N/A",
        "Event": "'OEM Event = 0001h'",
    },
    {
        "ID": "1",
        "Name": "SysHealth_Stat",
        "Type": "Chassis",
        "State": "Nominal",
        "Reading": "N/A",
        "Units": "N/A",
        "Event": "'transition to OK'",
    },
    {
        "ID": "2",
        "Name": "01-Inlet Ambient",
        "Type": "Temperature",
        "State": "Nominal",
        "Reading": "20.00",
        "Units": "C",
        "Event": "'OK'",
    },
]


class TestIpmiMonitoring(unittest.TestCase):
    """Test the IpmiMonitoring class."""

    @patch.object(Command, "__call__")
    def test_00_get_sensor_data_success(self, mock_call):
        with open(IPMIMONITORING_SAMPLE_OUTPUT, "r") as content:
            mock_call.return_value = Result(content.read(), None)
            config = Config()
            ipmimonitoring = IpmiMonitoring(config)
            payloads = ipmimonitoring.get_sensor_data()
            expected_sensor_entries = SAMPLE_SENSOR_ENTRIES
            self.assertEqual(payloads, expected_sensor_entries)

    @patch.object(Command, "__call__")
    def test_00_get_sensor_data_error(self, mock_call):
        mock_call.return_value = Result("", True)
        config = Config()
        ipmimonitoring = IpmiMonitoring(config)
        payloads = ipmimonitoring.get_sensor_data()
        self.assertEqual(payloads, [])
