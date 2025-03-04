import unittest
from unittest.mock import patch

from freezegun import freeze_time

from prometheus_hardware_exporter.collectors.ipmi_sel import IpmiSel
from prometheus_hardware_exporter.config import Config
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
            config = Config()
            ipmi_sel = IpmiSel(config)
            payloads = ipmi_sel.get_sel_entries(24 * 60 * 60)
            mock_call.assert_called_with(
                "--sdr-cache-recreate --output-event-state --interpret-oem-data --entity-sensor-names"
            )
            self.assertEqual(payloads, SAMPLE_SEL_ENTRIES)

    @patch.object(Command, "__call__")
    def test_01_get_sel_entries_zero_records(self, mock_call):
        mock_call.return_value = Result("", None)
        config = Config()
        ipmi_sel = IpmiSel(config)
        payloads = ipmi_sel.get_sel_entries(300)
        mock_call.assert_called_with(
            "--sdr-cache-recreate --output-event-state --interpret-oem-data --entity-sensor-names"
        )
        self.assertEqual(payloads, [])

    @patch.object(Command, "__call__")
    def test_02_get_sel_entries_error(self, mock_call):
        mock_call.return_value = Result("", Exception())
        config = Config()
        ipmi_sel = IpmiSel(config)
        payloads = ipmi_sel.get_sel_entries(300)
        mock_call.assert_called_with(
            "--sdr-cache-recreate --output-event-state --interpret-oem-data --entity-sensor-names"
        )
        self.assertEqual(payloads, None)

    @patch.object(Command, "__call__")
    @freeze_time("2023-07-09 12:00:00")
    def test_03_ttl_valid(self, mock_call):
        with open(SEL_SAMPLE_OUTPUT, "r") as content:
            mock_call.return_value = Result(content.read(), None)
            config = Config()
            config.ipmi_sel_cache_ttl = 5
            ipmi_sel = IpmiSel(config)
            payloads_first = ipmi_sel.get_sel_entries(300)
            self.assertEqual(payloads_first, SAMPLE_SEL_ENTRIES)

            with freeze_time("2023-07-09 12:00:04"):
                payloads_second = ipmi_sel.get_sel_entries(300)
                self.assertEqual(payloads_first, payloads_second)

    @patch.object(Command, "__call__")
    @freeze_time("2023-07-09 12:00:00")
    def test_04_ttl_expired(self, mock_call):
        with open(SEL_SAMPLE_OUTPUT, "r") as content:
            mock_call.return_value = Result(content.read(), None)
            config = Config()
            config.ipmi_sel_cache_ttl = 5
            ipmi_sel = IpmiSel(config)
            payloads = ipmi_sel.get_sel_entries(300)
            self.assertEqual(payloads, SAMPLE_SEL_ENTRIES)

            with freeze_time("2023-07-09 12:00:06"):
                payloads_second = ipmi_sel.get_sel_entries(300)
                self.assertEqual(payloads_second, None)
