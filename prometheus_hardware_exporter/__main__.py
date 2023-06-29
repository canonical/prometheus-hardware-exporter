"""Package entrypoint."""

import argparse
import logging
from typing import List

from .collector import COLLECTOR_REGISTRIES, RedfishCollector
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
    args = parser.parse_args()

    return args


def main(port: int, level: str, enable_collectors: List[str], daemon: bool = False) -> None:
    """Start the prometheus-hardware-exporter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.getLevelName(level))

    exporter = Exporter(port)
    enable_collectors_set = set(enable_collectors)
    for name, collector in COLLECTOR_REGISTRIES.items():
        if name.lower() in enable_collectors_set:
            logger.info("%s is enabled", name)
            exporter.register(collector)
    exporter.run(daemon)


if __name__ == "__main__":  # pragma: no cover
    ns = parse_command_line()
    if ns.config:
        config = Config.load_config(config_file=ns.config or DEFAULT_CONFIG)
    else:
        collectors = []
        for args_name, enable in ns.__dict__.items():
            if args_name.startswith("collector") and enable:
                collectors.append(args_name)
        config = Config(port=ns.port, level=ns.level, enable_collectors=collectors)

    # Start the exporter
    main(config.port, config.level, config.enable_collectors)
