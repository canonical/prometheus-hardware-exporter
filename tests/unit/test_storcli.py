import json
import unittest
from unittest.mock import patch

from prometheus_hardware_exporter.collectors.storcli import StorCLI
from prometheus_hardware_exporter.config import Config
from prometheus_hardware_exporter.utils import Command, Result

CALL_SHOW_ALL = "tests/unit/test_resources/storcli/cALL_show_all.txt"


class TestStorCLI(unittest.TestCase):
    """Test StorCLI class."""

    @patch.object(Command, "__call__")
    def test_00__extract_enclosures_fail(self, mock_call):
        config = Config()
        storcli = StorCLI(config)
        payload = storcli._extract_enclosures({})
        self.assertEqual(payload, [])

    @patch.object(Command, "__call__")
    def test_01__extract_virtual_drives_fail(self, mock_call):
        config = Config()
        storcli = StorCLI(config)
        payload = storcli._extract_virtual_drives({})
        self.assertEqual(payload, [])

    @patch.object(Command, "__call__")
    def test_03__extract_physical_drives_fail(self, mock_call):
        config = Config()
        storcli = StorCLI(config)
        payload = storcli._extract_physical_drives({})
        self.assertEqual(payload, [])

    @patch.object(Command, "__call__")
    def test_10_get_all_information_okay(self, mock_call):
        with open(CALL_SHOW_ALL, "r") as content:
            mock_call.return_value = Result(content.read(), None)
            config = Config()
            storcli = StorCLI(config)
            payload = storcli.get_all_information()
            expected_payload = {
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
                        {
                            "EID:Slt": "251:2",
                            "DID": 1,
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
            self.assertEqual(payload, expected_payload)

    @patch.object(Command, "__call__")
    def test_11_get_all_information_fail(self, mock_call):
        mock_controllers = json.dumps({"Controllers": [{}]})
        mock_call.return_value = Result(mock_controllers, None)
        config = Config()
        storcli = StorCLI(config)
        payload = storcli.get_all_information()
        expected_payload = {}
        self.assertEqual(payload, expected_payload)

    @patch.object(Command, "__call__")
    def test_12_get_all_information_error(self, mock_call):
        mock_call.return_value = Result(error="error")
        config = Config()
        storcli = StorCLI(config)
        payload = storcli.get_all_information()
        expected_payload = {}
        self.assertEqual(payload, expected_payload)
