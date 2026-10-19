from unittest.mock import Mock, patch

import pytest

from prometheus_hardware_exporter import __main__
from prometheus_hardware_exporter.__main__ import (
    get_collector_registries,
    main,
    parse_command_line,
    start_exporter,
)
from prometheus_hardware_exporter.collectors.ipmi_dcmi import IpmiTool
from prometheus_hardware_exporter.config import Config


class TestCli:
    """Cli test class."""

    @patch("argparse.ArgumentParser")
    def test_parse_argument(self, mock_argument_parser):
        parse_command_line()
        mock_argument_parser.assert_called_once()

    @patch.object(__main__, "Config")
    @patch.object(__main__, "start_exporter")
    @patch.object(__main__, "parse_command_line")
    def test_cli_main_with_config_file(self, mock_parse_cli, mock_start_exporter, mock_config):
        mock_ns = Mock()
        mock_ns.config = Mock()
        mock_parse_cli.return_value = mock_ns
        mock_config.load_config.return_value = Mock()
        main()
        mock_config.load_config.assert_called_once_with(config_file=mock_ns.config)

    @patch.object(__main__, "Config")
    @patch.object(__main__, "start_exporter")
    @patch.object(__main__, "parse_command_line")
    def test_cli_main_with_arguments(self, mock_parse_cli, mock_start_exporter, mock_config):
        mock_ns = Mock()
        mock_ns.config = False
        mock_ns.collector_redfish = True
        mock_parse_cli.return_value = mock_ns
        mock_config.load_config.return_value = Mock()
        main()
        mock_config.assert_called_once()

    @patch.object(__main__, "Exporter")
    def test_start_exporter(self, mock_exporter):
        mock_port = 10000
        mock_level = "INFO"
        mock_enable_collectors = ["collector.mega_raid"]
        config = Config(port=mock_port, level=mock_level, enable_collectors=mock_enable_collectors)
        start_exporter(config)
        mock_exporter.assert_called_once_with(mock_port, addr="127.0.0.1")

    @pytest.mark.parametrize(
        "enable_collectors",
        [
            (["collector.mega_raid"]),
            (["collector.ipmi_dcmi", "collector.ipmi_sel", "collector.ipmi_sensor"]),
            (["collector.lsi_sas_2", "collector.lsi_sas_3"]),
            (["collector.mega_raid", "collector.poweredge_raid"]),
        ],
    )
    @patch.object(__main__, "Exporter")
    def test_cli_start_exporter_enable_collector(self, mock_exporter, enable_collectors):
        config = Config(port=10000, level="INFO", enable_collectors=enable_collectors)

        collector_registries = get_collector_registries(config)

        for collector in enable_collectors:
            if collector in collector_registries:
                collector_registries[collector] = Mock()

        with patch.object(__main__, "get_collector_registries", return_value=collector_registries):
            start_exporter(config)

        for collector in enable_collectors:
            mock_exporter.return_value.register.assert_any_call(
                collector_registries.get(collector)
            )

        for name, collector in collector_registries.items():
            if name.lower() not in enable_collectors:
                with pytest.raises(AssertionError):
                    mock_exporter.return_value.register.assert_called_with(collector)


def test_get_collector_registries():
    """Assert all the keys."""
    config = Config(port=10000, level="INFO", enable_collectors=[])

    # Every time someone add/remove collector should change this.
    collector_registries = get_collector_registries(config)

    assert set(collector_registries.keys()) == set(
        [
            "collector.adaptec_raid",
            "collector.hpe_ssa",
            "collector.ipmi_dcmi",
            "collector.ipmi_sel",
            "collector.ipmi_sensor",
            "collector.lsi_sas_2",
            "collector.lsi_sas_3",
            "collector.mega_raid",
            "collector.poweredge_raid",
            "collector.redfish",
        ]
    )


@patch.object(IpmiTool, "get_ipmi_host")
@patch.object(__main__, "start_exporter")
@patch.object(__main__, "parse_command_line")
def test_main_resolves_hostname_from_ipmitool(mock_parse_cli, mock_start_exporter, mock_get_bmc):
    """When no hostname provided, main should resolve it via get_bmc_address."""
    mock_ns = Mock()
    mock_ns.config = False
    mock_ns.port = 10000
    mock_ns.level = "INFO"
    mock_ns.hostname = ""
    mock_ns.username = ""
    mock_ns.password = ""
    mock_ns.driver_type = ""
    mock_ns.ipmi_sel_interval = 0
    mock_ns.redfish_client_timeout = 15
    mock_ns.redfish_client_max_retry = 1
    mock_ns.redfish_discover_cache_ttl = 86400
    mock_ns.collect_timeout = 30
    mock_ns.bind_address = "127.0.0.1"
    mock_ns.arcconf_path = "/usr/sbin/arcconf"
    mock_ns.collection_timeout = 100
    mock_parse_cli.return_value = mock_ns

    mock_get_bmc.return_value = "1.2.3.4"

    main()

    mock_get_bmc.assert_called_once()
    assert mock_start_exporter.called
    exporter_config = mock_start_exporter.call_args[0][0]
    assert exporter_config.hostname == "1.2.3.4"


@patch.object(IpmiTool, "get_ipmi_host")
@patch.object(__main__, "start_exporter")
@patch.object(__main__, "parse_command_line")
def test_main_hostname_unresolved_warns(mock_parse_cli, mock_start_exporter, mock_get_bmc):
    """When get_bmc_address returns None, hostname remains empty."""
    mock_ns = Mock()
    mock_ns.config = False
    mock_ns.port = 10000
    mock_ns.level = "INFO"
    mock_ns.hostname = ""
    mock_ns.username = ""
    mock_ns.password = ""
    mock_ns.driver_type = ""
    mock_ns.ipmi_sel_interval = 0
    mock_ns.redfish_client_timeout = 15
    mock_ns.redfish_client_max_retry = 1
    mock_ns.redfish_discover_cache_ttl = 86400
    mock_ns.collect_timeout = 30
    mock_ns.bind_address = "127.0.0.1"
    mock_ns.arcconf_path = "/usr/sbin/arcconf"
    mock_ns.collection_timeout = 100
    mock_parse_cli.return_value = mock_ns

    mock_get_bmc.return_value = None

    main()

    mock_get_bmc.assert_called_once()
    assert mock_start_exporter.called
    exporter_config = mock_start_exporter.call_args[0][0]
    assert exporter_config.hostname == ""


@pytest.mark.parametrize(
    "options,address,path,budget",
    [
        ([], "127.0.0.1", "/usr/sbin/arcconf", 100),
        (
            [
                "--bind-address",
                "0.0.0.0",
                "--arcconf-path",
                "/opt/adaptec/arcconf",
                "--collection-timeout",
                "90",
            ],
            "0.0.0.0",
            "/opt/adaptec/arcconf",
            90,
        ),
    ],
)
def test_contract_cli_defaults_and_overrides(monkeypatch, options, address, path, budget):
    monkeypatch.setattr("sys.argv", ["exporter", "--hostname", "bmc", *options])
    with patch.object(__main__, "start_exporter") as start:
        main()
    config = start.call_args.args[0]
    assert config.bind_address == address
    assert config.arcconf_path == path
    assert config.collection_timeout == budget


def test_start_exporter_bind_override():
    with patch.object(__main__, "Exporter") as exporter:
        with patch.object(__main__, "get_collector_registries", return_value={}):
            start_exporter(Config(bind_address="192.0.2.1"))
    exporter.assert_called_once_with(10000, addr="192.0.2.1")
