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
            "driver_type": "LAN_2_0",
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


def test_collector_contract_defaults():
    config = Config()
    assert config.bind_address == "127.0.0.1"
    assert config.arcconf_path == "/usr/sbin/arcconf"
    assert config.collect_timeout == 30
    assert config.collection_timeout == 100


def test_collector_contract_yaml_overrides(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        "bind_address: 192.0.2.1\narcconf_path: /opt/adaptec/arcconf\n"
        "collection_timeout: 90\ncollect_timeout: 15\n"
    )
    config = Config.load_config(str(path))
    assert config.bind_address == "192.0.2.1"
    assert config.arcconf_path == "/opt/adaptec/arcconf"
    assert config.collection_timeout == 90
    assert config.collect_timeout == 15


@pytest.mark.parametrize("budget", [0, -1, 110.1, 120, float("inf"), float("nan"), None])
def test_invalid_collection_budget(budget):
    with pytest.raises(ValueError):
        Config(collection_timeout=budget)


@pytest.mark.parametrize("path", ["arcconf", "./arcconf", "", "/usr/sbin/arcconf\x00"])
def test_invalid_arcconf_path(path):
    with pytest.raises(ValueError):
        Config(arcconf_path=path)


@pytest.mark.parametrize("address", ["", " ", " 127.0.0.1"])
def test_invalid_bind_address(address):
    with pytest.raises(ValueError):
        Config(bind_address=address)


def test_collection_budget_maximum():
    assert Config(collection_timeout=110).collection_timeout == 110
