import unittest
from unittest.mock import Mock

from prometheus_hardware_exporter.collector import (
    LSISASControllerCollector,
    MegaRAIDCollector,
)


class TestCustomCollector(unittest.TestCase):
    """Custom test class."""

    def test_00_mega_raid_collector_not_installed(self):
        """Test mega raid collector when storcli is not installed."""
        mega_raid_collector = MegaRAIDCollector()
        mega_raid_collector.sasircu = Mock()
        mega_raid_collector.sasircu.installed = False
        payloads = mega_raid_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_01_mega_raid_collector_installed_and_okay(self):
        """Test mega raid collector can fetch correct number of metrics."""
        mega_raid_collector = MegaRAIDCollector()
        mega_raid_collector.storcli = Mock()
        mega_raid_collector.storcli.installed = True

        mock_controllers = {
            0: {
                "enclosures": [
                    {
                        "EID": 251,
                        "State": "OK",
                        "Slots": 2,
                        "PD": 2,
                        "PS": 0,
                        "Fans": 0,
                        "TSs": 0,
                        "Alms": 0,
                        "SIM": 0,
                        "Port#": "2I",
                    }
                ],
                "virtual_drives": [
                    {
                        "DG/VD": "0/239",
                        "TYPE": "RAID1",
                        "State": "Optl",
                        "Access": "RW",
                        "Consist": "Yes",
                        "Cache": "NRWTD",
                        "Cac": "-",
                        "sCC": "ON",
                        "Size": "744.687 GiB",
                        "Name": "NVMe-RAID-1",
                    }
                ],
                "physical_drives": [
                    {
                        "EID:Slt": "251:1",
                        "DID": 0,
                        "State": "Onln",
                        "DG": 0,
                        "Size": "800.00 GB",
                        "Intf": "NVMe",
                        "Med": "SSD",
                        "SED": "N",
                        "PI": "N",
                        "SeSz": "512B",
                        "Model": "MZXLR800HBHQ-000H3                      ",
                        "Sp": "U",
                        "Type": "-",
                    },
                ],
            }
        }
        mega_raid_collector.storcli.get_all_information.return_value = mock_controllers

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
