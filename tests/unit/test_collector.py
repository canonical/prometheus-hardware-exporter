import unittest
from unittest.mock import Mock

from prometheus_hardware_exporter.collector import MegaRAIDCollector


class TestCustomCollector(unittest.TestCase):
    """Custom test class."""

    @classmethod
    def setUpClass(cls):
        cls.mock_config = Mock()

    def test_00_mega_raid_collector_not_installed(self):
        """Test mega raid collector when storcli is not installed."""
        mega_raid_collector = MegaRAIDCollector(self.mock_config)
        payloads = mega_raid_collector.collect()

        self.assertEqual(len(list(payloads)), 1)

    def test_01_mega_raid_collector_installed_and_okay(self):
        """Test mega raid collector can fetch correct number of metrics."""
        mega_raid_collector = MegaRAIDCollector(self.mock_config)
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
        mega_raid_collector.storcli.get_controllers.return_value = mock_controller_payload, False
        mega_raid_collector.storcli.get_all_virtual_drives.return_value = (
            mock_virtual_drives_payload,
            False,
        )

        payloads = mega_raid_collector.collect()

        available_metrics = [spec.name for spec in mega_raid_collector.specifications]
        self.assertEqual(len(list(payloads)), len(available_metrics))
        for payload in payloads:
            self.assertIn(payload.name, available_metrics)
