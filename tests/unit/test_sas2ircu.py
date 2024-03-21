import unittest
from unittest.mock import patch

from prometheus_hardware_exporter.collectors.sasircu import Sasircu
from prometheus_hardware_exporter.config import Config
from prometheus_hardware_exporter.utils import Command, Result

LIST = "tests/unit/test_resources/sas2ircu/list.txt"
DISPLAY_HAS_VOLUMES = "tests/unit/test_resources/sas2ircu/display_has_volume.txt"
DISPLAY_NO_VOLUMES = "tests/unit/test_resources/sas2ircu/display_no_volume.txt"


class TestSasircu(unittest.TestCase):
    """Test Sasircu class."""

    @patch.object(Command, "__call__")
    def test_00_list_okay(self, mock_call):
        with open(LIST, "r") as content:
            mock_call.return_value = Result(content.read(), None)
            config = Config()
            sas2ircu = Sasircu(config, 2)
            adapters = sas2ircu.get_adapters()
            expected_adapters = {
                "0": {
                    "Index": "0",
                    "Adapter Type": "SAS2008",
                    "Vendor ID": "1000h",
                    "Device ID": "72h",
                    "Pci Address": "00h:05h:00h:00h",
                    "SubSys Ven ID": "1028h",
                    "SubSys Dev ID": "1f1eh",
                },
                "1": {
                    "Index": "1",
                    "Adapter Type": "SAS2009",
                    "Vendor ID": "1001h",
                    "Device ID": "73h",
                    "Pci Address": "00h:05h:00h:01h",
                    "SubSys Ven ID": "1029h",
                    "SubSys Dev ID": "1f1fh",
                },
            }
            self.assertEqual(adapters, expected_adapters)

    @patch.object(Command, "__call__")
    def test_01_list_failed(self, mock_call):
        mock_call.return_value = Result("", None)
        config = Config()
        sas2ircu = Sasircu(config, 2)
        adapters = sas2ircu.get_adapters()
        self.assertEqual(adapters, {})

    @patch.object(Command, "__call__")
    def test_10_get_all_information_has_volume(self, mock_call):
        with open(DISPLAY_HAS_VOLUMES, "r") as content:
            mock_call.return_value = Result(content.read(), None)
            config = Config()
            sas2ircu = Sasircu(config, 2)
            information = sas2ircu.get_all_information(0)
            expected_information = {
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
                            "PHY[1] Enclosure#/Slot#": "1:1",
                        },
                    }
                },
                "enclosures": {
                    "1": {
                        "Enclosure#": "1",
                        "Logical ID": "5782bcb0:19e35100",
                        "Numslots": "9",
                        "StartSlot": "0",
                    },
                    "2": {
                        "Enclosure#": "2",
                        "Logical ID": "5782bcb0:19e35101",
                        "Numslots": "10",
                        "StartSlot": "0",
                    },
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
                    "1:1": {
                        "Enclosure #": "1",
                        "Slot #": "1",
                        "SAS Address": "4433221-1-0600-0000",
                        "State": "Ready (RDY)",
                        "Size (in MB)/(in sectors)": "476940/976773167",
                        "Manufacturer": "ATA",
                        "Model Number": "ST9500620NS",
                        "Firmware Revision": "AA0D",
                        "Serial No": "9XF3QNC7",
                        "GUID": "5000c5007bc22d2b",
                        "Protocol": "SATA",
                        "Drive Type": "SATA_HDD",
                    },
                },
            }

            self.assertEqual(information, expected_information)

    @patch.object(Command, "__call__")
    def test_11_get_all_information_no_volumes(self, mock_call):
        with open(DISPLAY_NO_VOLUMES, "r") as content:
            mock_call.return_value = Result(content.read(), None)
            config = Config()
            sas2ircu = Sasircu(config, 2)
            information = sas2ircu.get_all_information(0)
            expected_information = {
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
                "ir_volumes": {},
                "enclosures": {
                    "1": {
                        "Enclosure#": "1",
                        "Logical ID": "5782bcb0:19e35100",
                        "Numslots": "9",
                        "StartSlot": "0",
                    },
                    "2": {
                        "Enclosure#": "2",
                        "Logical ID": "5782bcb0:19e35101",
                        "Numslots": "10",
                        "StartSlot": "0",
                    },
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
                    "1:1": {
                        "Enclosure #": "1",
                        "Slot #": "1",
                        "SAS Address": "4433221-1-0600-0000",
                        "State": "Ready (RDY)",
                        "Size (in MB)/(in sectors)": "476940/976773167",
                        "Manufacturer": "ATA",
                        "Model Number": "ST9500620NS",
                        "Firmware Revision": "AA0D",
                        "Serial No": "9XF3QNC7",
                        "GUID": "5000c5007bc22d2b",
                        "Protocol": "SATA",
                        "Drive Type": "SATA_HDD",
                    },
                },
            }
            self.assertEqual(information, expected_information)

    @patch.object(Command, "__call__")
    def test_20_get_all_information_failed(self, mock_call):
        mock_call.return_value = Result("some content", True)
        config = Config()
        sas2ircu = Sasircu(config, 2)
        information = sas2ircu.get_all_information(0)
        expected_information = {}
        self.assertEqual(information, expected_information)

    @patch.object(Command, "__call__")
    def test_21_get_all_information_failed(self, mock_call):
        mock_call.return_value = Result("", None)
        config = Config()
        sas2ircu = Sasircu(config, 2)
        information = sas2ircu.get_all_information(0)
        expected_information = {}
        self.assertEqual(information, expected_information)

    @patch.object(Command, "__call__")
    def test_30_get_adapters_failed(self, mock_call):
        mock_call.return_value = Result("", True)
        config = Config()
        sas2ircu = Sasircu(config, 2)
        adapters = sas2ircu.get_adapters()
        expected_adapters = {}
        self.assertEqual(adapters, expected_adapters)

    def test_40__parse_key_value_failed(self):
        config = Config()
        sas2ircu = Sasircu(config, 2)
        kv = sas2ircu._parse_key_value("")
        expected_kv = {}
        self.assertEqual(kv, expected_kv)

    def test_50__get_controller_failed(self):
        config = Config()
        sas2ircu = Sasircu(config, 2)
        controllers = sas2ircu._get_controller("")
        expected_controllers = {}
        self.assertEqual(controllers, expected_controllers)

    def test_60__get_physical_disks(self):
        config = Config()
        sas2ircu = Sasircu(config, 2)
        topology = sas2ircu._get_physical_disks("")
        expected_topology = {}
        self.assertEqual(topology, expected_topology)

    def test_70__get_enclosures_failed(self):
        config = Config()
        sas2ircu = Sasircu(config, 2)
        enclosures = sas2ircu._get_enclosures("")
        expected_enclosures = {}
        self.assertEqual(enclosures, expected_enclosures)
