"""Package entrypoint."""

import argparse
import logging

from .collector import (
    IpmiDcmiCollector,
    IpmiSelCollector,
    IpmiSensorsCollector,
    LSISASControllerCollector,
    MegaRAIDCollector,
    PowerEdgeRAIDCollector,
    RedfishCollector,
    SsaCLICollector,
)
from .config import DEFAULT_CONFIG, Config
from .exporter import Exporter

logger = logging.getLogger(__name__)


def parse_command_line() -> argparse.Namespace:
    """Command line parser.

    Parse command line arguments and return the arguments.

    Returns:
        args: Command line arguments.
    """
    parser = argparse.ArgumentParser(
        prog=__package__,
        description=__doc__,
    )
    parser.add_argument("-l", "--level", help="Set logging level.", default="INFO", type=str)
    parser.add_argument("-c", "--config", help="Set configuration file.", default="", type=str)
    parser.add_argument(
        "-p",
        "--port",
        help="Address on which to expose metrics and web interface.",
        default=10000,
        type=int,
    )
    parser.add_argument(
        "--redfish-host",
        help="Hostname for redfish collector",
        default="127.0.0.1",
        type=str,
    )
    parser.add_argument(
        "--redfish-username",
        help="BMC username for redfish collector",
        default="",
        type=str,
    )
    parser.add_argument(
        "--redfish-password",
        help="BMC password for redfish collector",
        default="",
        type=str,
    )
    parser.add_argument(
        "--collector.hpe_ssa",
        help="Enable HPE Smart Array Controller collector (default: disabled)",
        action="store_true",
    )
    parser.add_argument(
        "--collector.ipmi_dcmi",
        help="Enable IPMI dcmi collector (default: disabled)",
        action="store_true",
    )
    parser.add_argument(
        "--collector.ipmi_sel",
        help="Enable IPMI sel collector (default: disabled)",
        action="store_true",
    )
    parser.add_argument(
        "--collector.ipmi_sensor",
        help="Enable IPMI sensor collector (default: disabled)",
        action="store_true",
    )
    parser.add_argument(
        "--collector.lsi_sas_2",
        help="Enable LSI SAS-2 controller collector (default: disabled)",
        action="store_true",
    )
    parser.add_argument(
        "--collector.lsi_sas_3",
        help="Enable LSI SAS-3 controller collector (default: disabled)",
        action="store_true",
    )
    parser.add_argument(
        "--collector.mega_raid",
        help="Enable MegaRAID collector (default: disabled)",
        action="store_true",
    )
    parser.add_argument(
        "--collector.poweredge_raid",
        help="Enable PowerEdge RAID controller collector (default: disabled)",
        action="store_true",
    )
    parser.add_argument(
        "--collector.redfish",
        help="Enable redfish collector (default: disabled)",
        action="store_true",
    )
    args = parser.parse_args()

    return args


def start_exporter(config: Config, daemon: bool = False) -> None:
    """Start the prometheus-hardware-exporter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.getLevelName(config.level))

    exporter = Exporter(config.port)
    enable_collectors_set = set(config.enable_collectors)
    collector_registries = {
        "collector.hpe_ssa": SsaCLICollector(config),
        "collector.ipmi_dcmi": IpmiDcmiCollector(config),
        "collector.ipmi_sel": IpmiSelCollector(config),
        "collector.ipmi_sensor": IpmiSensorsCollector(config),
        "collector.lsi_sas_2": LSISASControllerCollector(version=2, config=config),
        "collector.lsi_sas_3": LSISASControllerCollector(version=3, config=config),
        "collector.mega_raid": MegaRAIDCollector(config),
        "collector.poweredge_raid": PowerEdgeRAIDCollector(config),
        "collector.redfish": RedfishCollector(config),
    }
    for name, collector in collector_registries.items():
        if name.lower() in enable_collectors_set:
            logger.info("%s is enabled", name)
            exporter.register(collector)
    exporter.run(daemon)


def main() -> None:
    """Entrypoint of the package."""
    namespace = parse_command_line()
    if namespace.config:
        exporter_config = Config.load_config(config_file=namespace.config or DEFAULT_CONFIG)
    else:
        collectors = []
        for args_name, enable in namespace.__dict__.items():
            if args_name.startswith("collector") and enable:
                collectors.append(args_name)
        exporter_config = Config(
            port=namespace.port,
            level=namespace.level,
            enable_collectors=collectors,
            redfish_host=namespace.redfish_host,
            redfish_username=namespace.redfish_username,
            redfish_password=namespace.redfish_password,
        )

    # Start the exporter
    start_exporter(exporter_config)


if __name__ == "__main__":  # pragma: no cover
    main()
