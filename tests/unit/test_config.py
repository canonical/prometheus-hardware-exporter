import unittest
from unittest.mock import patch

import pytest

from prometheus_hardware_exporter.__main__ import Config


class TestConfig(unittest.TestCase):
    """Config test class."""

    def setUp(self):
        self.patch_open_file = patch("builtins.open")
        self.patch_os_path_exists = patch("os.path.exists", return_value=True)
        self.patch_open_file.start()
        self.patch_os_path_exists.start()

    def tearDown(self):
        self.patch_open_file.stop()
        self.patch_os_path_exists.stop()

    @patch("prometheus_hardware_exporter.config.safe_load")
    def test_valid_config(self, mock_safe_load):
        """Test valid config."""
        mock_port = 10000
        mock_level = "INFO"
        mock_enable_collectors = [
            "collector.hpe_ssa",
            "collector.ipmi_dcmi",
            "collector.ipmi_sel",
            "collector.ipmi_sensor",
            "collector.lsi_sas_2",
            "collector.lsi_sas_3",
            "collector.mega_raid",
            "collector.poweredge_raid",
        ]
        mock_safe_load.return_value = {
            "port": mock_port,
            "level": mock_level,
            "enable_collectors": mock_enable_collectors,
        }
        config = Config.load_config()
        self.assertEqual(config.port, mock_port)
        self.assertEqual(config.level, mock_level)
        self.assertEqual(config.enable_collectors, mock_enable_collectors)

    @patch("prometheus_hardware_exporter.config.safe_load")
    def test_invalid_config(self, mock_safe_load):
        """Test invalid config."""
        mock_port = -10000
        mock_level = "RANDOM"
        mock_enable_collectors = ["collector.unknown"]
        mock_safe_load.return_value = {
            "port": mock_port,
            "level": mock_level,
            "enable_collectors": mock_enable_collectors,
        }
        with pytest.raises(ValueError):
            Config.load_config()

    def test_missing_config(self):
        """Test missing config."""
        self.patch_open_file.stop()
        self.patch_os_path_exists.stop()
        with pytest.raises(ValueError):
            Config.load_config("random")
