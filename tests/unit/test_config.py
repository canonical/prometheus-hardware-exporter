import unittest
from unittest.mock import patch

import pytest

from prometheus_hardware_exporter.__main__ import Config
from prometheus_hardware_exporter.config import get_bmc_address
import subprocess


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
            "driver_type": "LAN_2_0"
        }
        with pytest.raises(ValueError):
            Config.load_config()

    @patch("prometheus_hardware_exporter.config.safe_load")
    def test_invalid_driver_config(self, mock_safe_load):
        """Test invalid driver config."""
        mock_safe_load.return_value = {
            "driver_type": "RANDOM",
        }
        with pytest.raises(ValueError):
            Config.load_config()

    def test_missing_config(self):
        """Test missing config."""
        self.patch_open_file.stop()
        self.patch_os_path_exists.stop()
        with pytest.raises(ValueError):
            Config.load_config("random")


@patch("prometheus_hardware_exporter.config.subprocess.check_output")
def test_get_bmc_address_success(mock_check_output):
    """get_bmc_address should return IP when ipmitool prints it."""
    mock_check_output.return_value = (
        "Some header\nIP Address              : 1.2.3.4\nOther: value"
    )
    assert get_bmc_address() == "1.2.3.4"


@patch("prometheus_hardware_exporter.config.subprocess.check_output")
def test_get_bmc_address_failure(mock_check_output):
    """get_bmc_address should return None when ipmitool is unavailable."""
    mock_check_output.side_effect = subprocess.CalledProcessError(1, "ipmitool")
    assert get_bmc_address() is None


@patch("prometheus_hardware_exporter.config.subprocess.check_output")
def test_get_bmc_address_no_host(mock_check_output):
    """get_bmc_address should return None when no IP Address line present."""
    mock_check_output.return_value = "No ip information here\nAnother line"
    assert get_bmc_address() is None
