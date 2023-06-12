import unittest
from unittest.mock import Mock

from prometheus_hardware_exporter.collector import (
    IpmiDcmiCollector,
    IpmiSelCollector,
    IpmiSensorsCollector,
    MegaRAIDCollector,
)

SAMPLE_IPMI_SEL_ENTRIES = [
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
SAMPLE_IPMI_SENSOR_ENTRIES = [
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
    {
        "ID": "3",
        "Name": "Power Meter",
        "Type": "Other Units Based Sensor",
        "State": "Nominal",
        "Reading": "0.00",
        "Units": "W",
        "Event": "'OK'",
    },
    {
        "ID": "4",
        "Name": "Current meter",
        "Type": "Current",
        "State": "Nominal",
        "Reading": "22.00",
        "Units": "A",
        "Event": "'OK'",
    },
    {
        "ID": "5",
        "Name": "Fan meter",
        "Type": "Fan",
        "State": "Nominal",
        "Reading": "2200.00",
        "Units": "RPM",
        "Event": "'OK'",
    },
    {
        "ID": "6",
        "Name": "Volt Meter",
        "Type": "Other Units Based Sensor",
        "State": "Nominal",
        "Reading": "220.00",
        "Units": "V",
        "Event": "'OK'",
    },
    {
        "ID": "6",
        "Name": "Fan Meter",
        "Type": "Fan",
        "State": "Nominal",
        "Reading": "61.00",
        "Units": "%",
        "Event": "'OK'",
    },
    {
        "ID": "6",
        "Name": "Test meter",
        "Type": "Sample generic sensor",
        "State": "Nominal",
        "Reading": "54.00",
        "Units": "%",
        "Event": "'OK'",
    },
]


class TestCustomCollector(unittest.TestCase):
    """Custom test class."""

    def test_00_mega_raid_collector_not_installed(self):
        """Test mega raid collector when storcli is not installed."""
        mega_raid_collector = MegaRAIDCollector()
        payloads = mega_raid_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_01_mega_raid_collector_installed_and_okay(self):
        """Test mega raid collector can fetch correct number of metrics."""
        mega_raid_collector = MegaRAIDCollector()
        mega_raid_collector.storcli = Mock()

        mock_controller_payload = {"count": 1, "hostname": "kongfu"}
        mock_virtual_drives_payload = {
            "0": [
                {
                    "DG": 0,
                    "VD": 239,
                    "state": "Optl",
                    "cache": "NRWTD",
                }
            ],
        }
        mega_raid_collector.storcli.get_controllers.return_value = mock_controller_payload
        mega_raid_collector.storcli.get_all_virtual_drives.return_value = (
            mock_virtual_drives_payload
        )

        payloads = mega_raid_collector.collect()

        available_metrics = [spec.name for spec in mega_raid_collector.specifications]
        self.assertEqual(len(list(payloads)), len(available_metrics))
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)

    def test_10_ipmi_dcmi_collector_not_installed(self):
        """Test ipmi dcmi collector when ipmi-dcmi is not installed."""
        ipmi_dcmi_collector = IpmiDcmiCollector()
        payloads = ipmi_dcmi_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_11_ipmi_dcmi_collector_installed_and_okay(self):
        """Test ipmi dcmi collector can fetch correct number of metrics."""
        ipmi_dcmi_collector = IpmiDcmiCollector()
        ipmi_dcmi_collector.ipmi_dcmi = Mock()

        mock_dcmi_payload = {"current_power": 105}

        ipmi_dcmi_collector.ipmi_dcmi.get_current_power.return_value = mock_dcmi_payload

        payloads = ipmi_dcmi_collector.collect()

        available_metrics = [spec.name for spec in ipmi_dcmi_collector.specifications]
        self.assertEqual(len(list(payloads)), len(available_metrics))
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)

    def test_20_ipmi_sel_not_installed(self):
        """Test ipmi sel collector when ipmi sel is not installed."""
        ipmi_sel_collector = IpmiSelCollector()
        payloads = ipmi_sel_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_21_ipmi_sel_installed_and_okay(self):
        """Test ipmi sel collector can fetch correct number of metrics."""
        ipmi_sel_collector = IpmiSelCollector()
        ipmi_sel_collector.ipmi_sel = Mock()

        mock_sel_entries = SAMPLE_IPMI_SEL_ENTRIES

        ipmi_sel_collector.ipmi_sel.get_sel_entries.return_value = mock_sel_entries

        payloads = ipmi_sel_collector.collect()

        available_metrics = [spec.name for spec in ipmi_sel_collector.specifications]
        self.assertEqual(len(list(payloads)), len(mock_sel_entries) + 1)
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)

    def test_30_ipmimonitoring_not_installed(self):
        """Test ipmi sensor collector when ipmimonitoring is not installed."""
        ipmi_sensors_collector = IpmiSensorsCollector()
        payloads = ipmi_sensors_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_31_ipmimonitoring_installed_and_okay(self):
        """Test ipmi sensors collector can fetch correct number of metrics."""
        ipmi_sensors_collector = IpmiSensorsCollector()
        ipmi_sensors_collector.ipmimonitoring = Mock()

        mock_sensor_data = SAMPLE_IPMI_SENSOR_ENTRIES

        ipmi_sensors_collector.ipmimonitoring.get_sensor_data.return_value = mock_sensor_data
        payloads = ipmi_sensors_collector.collect()

        available_metrics = [spec.name for spec in ipmi_sensors_collector.specifications]
        self.assertEqual(len(list(payloads)), len(mock_sensor_data) + 1)
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)
