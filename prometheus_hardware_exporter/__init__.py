"""Configuring global logger."""

import logging

logging.basicConfig(
    level=logging.WARNING,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s %(levelname)s %(message)s",
)
