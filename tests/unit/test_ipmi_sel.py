import unittest
from unittest.mock import patch

from prometheus_hardware_exporter.collectors.ipmi_sel import IpmiSel
from prometheus_hardware_exporter.utils import Command, Result

SEL_SAMPLE_OUTPUT = "tests/unit/test_resources/ipmi/ipmi_sel_sample_output.txt"
SAMPLE_SEL_ENTRIES = [
    {
        "ID": "493",
        "Date": "Oct-06-2022",
        "Time": "19:47:13",
        "Name": "System Board ACPI_Stat",
        "Type": "System ACPI Power State",
        "State": "Nominal",
        "Event": "S0/G0",
    },
    {
        "ID": "494",
        "Date": "Oct-06-2022",
        "Time": "19:57:23",
        "Name": "System Chassis SysHealth_Stat",
        "Type": "Chassis",
        "State": "Critical",
        "Event": "transition to Non-recoverable from less severe",
    },
    {
        "ID": "495",
        "Date": "Oct-06-2022",
        "Time": "19:57:38",
        "Name": "System Board ACPI_Stat",
        "Type": "System ACPI Power State",
        "State": "Nominal",
        "Event": "S4/S5 soft-off",
    },
    {
        "ID": "496",
        "Date": "Oct-06-2022",
        "Time": "19:57:51",
        "Name": "System Board ACPI_Stat",
        "Type": "System ACPI Power State",
        "State": "Nominal",
        "Event": "S0/G0",
    },
]


class TestIpmiSel(unittest.TestCase):
    """Test the IpmiSel class."""

    @patch.object(Command, "__call__")
    def test_00_get_sel_entries_success(self, mock_call):
        with open(SEL_SAMPLE_OUTPUT, "r") as content:
            mock_call.return_value = Result(content.read(), None)
            ipmi_sel = IpmiSel()
            payloads = ipmi_sel.get_sel_entries()
            expected_sel_entries = SAMPLE_SEL_ENTRIES
            self.assertEqual(payloads, expected_sel_entries)

    @patch.object(Command, "__call__")
    def test_01_get_sel_entries_error(self, mock_call):
        mock_call.return_value = Result("", True)
        ipmi_sel = IpmiSel()
        payloads = ipmi_sel.get_sel_entries()
        self.assertEqual(payloads, [])
