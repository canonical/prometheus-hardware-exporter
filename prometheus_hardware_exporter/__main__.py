"""Package entrypoint."""

import argparse
import logging

from .collector import MegaRAIDCollector
from .config import DEFAULT_CONFIG, Config
from .exporter import Exporter

root_logger = logging.getLogger()


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
    parser.add_argument("-c", "--config", help="Set configuration file.", default="", type=str)
    args = parser.parse_args()

    return args


def main() -> None:
    """Start the prometheus-hardware-exporter."""
    args = parse_command_line()
    config = Config.load_config(config_file=args.config or DEFAULT_CONFIG)
    root_logger.setLevel(logging.getLevelName(config.level))

    exporter = Exporter(config.port)
    exporter.register(MegaRAIDCollector())
    exporter.run()


if __name__ == "__main__":  # pragma: no cover
    main()
