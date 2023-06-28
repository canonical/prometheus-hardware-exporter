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
        mock_safe_load.return_value = {
            "port": 10000,
            "level": "INFO",
            "enable_collectors": ["mega-raid-collector"],
        }
        config = Config.load_config()
        self.assertEqual(config.port, 10000)
        self.assertEqual(config.level, "INFO")
        self.assertEqual(config.enable_collectors, ["mega-raid-collector"])

    @patch("prometheus_hardware_exporter.config.safe_load")
    def test_invalid_config(self, mock_safe_load):
        """Test invalid config."""
        mock_safe_load.return_value = {
            "port": -10000,
            "level": "RANDOM",
            "enable_collectors": ["megaraidcollector"],
        }
        with pytest.raises(ValueError):
            Config.load_config()

    def test_missing_config(self):
        """Test missing config."""
        self.patch_open_file.stop()
        self.patch_os_path_exists.stop()
        with pytest.raises(ValueError):
            Config.load_config("random")
