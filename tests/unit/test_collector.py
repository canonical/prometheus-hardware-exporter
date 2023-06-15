import unittest
from unittest.mock import Mock

from prometheus_hardware_exporter.collector import (
    IpmiDcmiCollector,
    IpmiSelCollector,
    IpmiSensorsCollector,
    LSISASControllerCollector,
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

    def test_10_lsi_sas_2_collector_not_installed(self):
        """Test LSI SAS 2 collector when sas2ircu is not installed."""
        lsi_sas_2_collector = LSISASControllerCollector(2)
        lsi_sas_2_collector.sasircu = Mock()
        lsi_sas_2_collector.sasircu.installed = False
        lsi_sas_2_collector.sasircu.get_adapters.return_value = {}
        lsi_sas_2_collector.sasircu.get_all_information.return_value = {}
        payloads = lsi_sas_2_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_11_lsi_sas_2_collector_installed_and_okay(self):
        """Test LSI SAS 2 collector can fetch correct number of metrics."""
        lsi_sas_2_collector = LSISASControllerCollector(2)
        lsi_sas_2_collector.sasircu = Mock()
        mock_adapters = {
            "0": {
                "Index": "0",
                "Adapter Type": "SAS2008",
                "Vendor ID": "1000h",
                "Device ID": "72h",
                "Pci Address": "00h:05h:00h:00h",
                "SubSys Ven ID": "1028h",
                "SubSys Dev ID": "1f1eh",
            },
        }
        mock_information = {
            "controller": {
                "Controller type": "SAS2008",
                "BIOS version": "7.11.10.00",
                "Firmware version": "7.15.08.00",
                "Channel description": "1 Serial Attached SCSI",
                "Initiator ID": "0",
                "Maximum physical devices": "39",
                "Concurrent commands supported": "2607",
                "Slot": "0",
                "Segment": "0",
                "Bus": "5",
                "Device": "0",
                "Function": "0",
                "RAID Support": "Yes",
            },
            "ir_volumes": {
                "1": {
                    "Volume ID": "286",
                    "PI Supported": "Yes",
                    "PI Enabled": "Yes",
                    "Status of volume": "Okay (OKY)",
                    "Volume wwid": "0677c0fb06777e7b",
                    "RAID level": "RAID1",
                    "Size (in MB)": "139236",
                    "Boot": "Primary",
                    "Physical hard disks": {
                        "PHY[0] Enclosure#/Slot#": "1:0",
                    },
                }
            },
            "enclosures": {
                "1": {
                    "Enclosure#": "1",
                    "Logical ID": "5782bcb0:19e35100",
                    "Numslots": "9",
                    "StartSlot": "0",
                }
            },
            "physical_disks": {
                "1:0": {
                    "Enclosure #": "1",
                    "Slot #": "0",
                    "SAS Address": "4433221-1-0700-0000",
                    "State": "Ready (RDY)",
                    "Size (in MB)/(in sectors)": "476940/976773167",
                    "Manufacturer": "ATA",
                    "Model Number": "ST9500620NS",
                    "Firmware Revision": "AA0D",
                    "Serial No": "9XF3RK3W",
                    "GUID": "5000c5007bc1cfd7",
                    "Protocol": "SATA",
                    "Drive Type": "SATA_HDD",
                },
            },
        }

        lsi_sas_2_collector.sasircu.installed = True
        lsi_sas_2_collector.sasircu.get_adapters.return_value = mock_adapters
        lsi_sas_2_collector.sasircu.get_all_information.return_value = mock_information

        payloads = lsi_sas_2_collector.collect()

        available_metrics = [spec.name for spec in lsi_sas_2_collector.specifications]
        self.assertEqual(len(list(payloads)), len(available_metrics))
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)

    def test_20_lsi_sas_3_collector_not_installed(self):
        """Test LSI SAS 3 collector when sas3ircu is not installed."""
        lsi_sas_3_collector = LSISASControllerCollector(3)
        lsi_sas_3_collector.sasircu = Mock()
        lsi_sas_3_collector.sasircu.installed = False
        lsi_sas_3_collector.sasircu.get_adapters.return_value = {}
        lsi_sas_3_collector.sasircu.get_all_information.return_value = {}
        payloads = lsi_sas_3_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_21_lsi_sas_3_collector_installed_and_okay(self):
        """Test LSI SAS 3 collector can fetch correct number of metrics."""
        lsi_sas_3_collector = LSISASControllerCollector(3)
        lsi_sas_3_collector.sasircu = Mock()
        mock_adapters = {
            "0": {
                "Index": "0",
                "Adapter Type": "SAS3004",
                "Vendor ID": "1000h",
                "Device ID": "97h",
                "Pci Address": "00h:01h:00h:00h",
                "SubSys Ven ID": "1028h",
                "SubSys Dev ID": "1f53h",
            },
        }
        mock_information = {
            "controller": {
                "Controller type": "SAS3008",
                "BIOS version": "8.37.02.00",
                "Firmware version": "16.00.11.00",
                "Channel description": "1 Serial Attached SCSI",
                "Initiator ID": "0",
                "Maximum physical devices": "543",
                "Concurrent commands supported": "9584",
                "Slot": "Unknown",
                "Segment": "0",
                "Bus": "1",
                "Device": "0",
                "Function": "0",
                "RAID Support": "No",
            },
            "ir_volumes": {
                "1": {
                    "Volume ID": "286",
                    "PI Supported": "Yes",
                    "PI Enabled": "Yes",
                    "Status of volume": "Okay (OKY)",
                    "Volume wwid": "0677c0fb06777e7b",
                    "RAID level": "RAID1",
                    "Size (in MB)": "139236",
                    "Boot": "Primary",
                    "Physical hard disks": {
                        "PHY[0] Enclosure#/Slot#": "1:0",
                    },
                }
            },
            "enclosures": {
                "1": {
                    "Enclosure#": "1",
                    "Logical ID": "52cea7f0:c5597b00",
                    "Numslots": "10",
                    "StartSlot": "0",
                },
            },
            "physical_disks": {
                "1:0": {
                    "Enclosure #": "1",
                    "Slot #": "0",
                    "SAS Address": "4433221-1-0400-0000",
                    "State": "Ready (RDY)",
                    "Size (in MB)/(in sectors)": "457862/937703087",
                    "Manufacturer": "ATA",
                    "Model Number": "HFS480G3H2X069N",
                    "Firmware Revision": "DZ00",
                    "Serial No": "BNA7N5994ICB47T3V",
                    "Unit Serial No(VPD)": "BNA7N5994ICB47T3V",
                    "GUID": "5ace42e02532f9e4",
                    "Protocol": "SATA",
                    "Drive Type": "SATA_SSD",
                },
            },
        }

        lsi_sas_3_collector.sasircu.installed = True
        lsi_sas_3_collector.sasircu.get_adapters.return_value = mock_adapters
        lsi_sas_3_collector.sasircu.get_all_information.return_value = mock_information

        payloads = lsi_sas_3_collector.collect()

        available_metrics = [spec.name for spec in lsi_sas_3_collector.specifications]
        self.assertEqual(len(list(payloads)), len(available_metrics))
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)

    def test_30_ipmi_dcmi_collector_not_installed(self):
        """Test ipmi dcmi collector when ipmi-dcmi is not installed."""
        ipmi_dcmi_collector = IpmiDcmiCollector()
        ipmi_dcmi_collector.ipmi_dcmi = Mock()
        ipmi_dcmi_collector.ipmi_dcmi.installed = False
        ipmi_dcmi_collector.ipmi_dcmi.get_current_power.return_value = {}
        payloads = ipmi_dcmi_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_31_ipmi_dcmi_collector_installed_and_okay(self):
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

    def test_40_ipmi_sel_not_installed(self):
        """Test ipmi sel collector when ipmi sel is not installed."""
        ipmi_sel_collector = IpmiSelCollector()
        ipmi_sel_collector.ipmi_sel = Mock()
        ipmi_sel_collector.ipmi_sel.installed = False
        ipmi_sel_collector.ipmi_sel.get_sel_entries.return_value = []
        payloads = ipmi_sel_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_41_ipmi_sel_installed_and_okay(self):
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

    def test_50_ipmimonitoring_not_installed(self):
        """Test ipmi sensor collector when ipmimonitoring is not installed."""
        ipmi_sensors_collector = IpmiSensorsCollector()
        ipmi_sensors_collector.ipmimonitoring = Mock()
        ipmi_sensors_collector.ipmimonitoring.installed = False
        ipmi_sensors_collector.ipmimonitoring.get_sensor_data.return_value = []
        payloads = ipmi_sensors_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_51_ipmimonitoring_installed_and_okay(self):
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
