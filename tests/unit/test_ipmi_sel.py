import unittest
from unittest.mock import patch

from freezegun import freeze_time

from prometheus_hardware_exporter.collectors.ipmi_sel import IpmiSel
from prometheus_hardware_exporter.utils import Command, Result

SEL_SAMPLE_OUTPUT = "tests/unit/test_resources/ipmi/ipmi_sel_sample_output.txt"
SAMPLE_SEL_ENTRIES = [
    {
        "ID": "14",
        "Date": "PostInit",
        "Time": "PostInit",
        "Name": "Disk Drive Bay 1 Cable SAS A",
        "Type": "Cable/Interconnect",
        "State": "Critical",
        "Event": "Configuration Error - Incorrect cable connected",
    },
    {
        "ID": "494",
        "Date": "Jul-09-2023",
        "Time": "13:56:23",
        "Name": "System Chassis SysHealth_Stat",
        "Type": "Chassis",
        "State": "Critical",
        "Event": "transition to Non-recoverable from less severe",
    },
    {
        "ID": "496",
        "Date": "Jul-09-2023",
        "Time": "13:57:50",
        "Name": "System Board ACPI_Stat",
        "Type": "System ACPI Power State",
        "State": "Nominal",
        "Event": "S0/G0",
    },
]


class TestIpmiSel(unittest.TestCase):
    """Test the IpmiSel class."""

    @patch.object(Command, "__call__")
    @freeze_time("2023-07-09 23:59:59")
    def test_00_get_sel_entries_success(self, mock_call):
        with open(SEL_SAMPLE_OUTPUT, "r") as content:
            mock_call.return_value = Result(content.read(), None)
            ipmi_sel = IpmiSel()
            payloads = ipmi_sel.get_sel_entries(24 * 60 * 60)
            expected_sel_entries = SAMPLE_SEL_ENTRIES
            print(payloads)
            self.assertEqual(payloads, expected_sel_entries)

    @patch.object(Command, "__call__")
    def test_01_get_sel_entries_error(self, mock_call):
        mock_call.return_value = Result("", True)
        ipmi_sel = IpmiSel()
        payloads = ipmi_sel.get_sel_entries(300)
        self.assertEqual(payloads, [])
