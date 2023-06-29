"""Module for hardware exporter related configuration."""

import os
from logging import getLogger
from typing import List

from pydantic import BaseModel, validator
from yaml import safe_load

logger = getLogger(__name__)

DEFAULT_CONFIG = os.path.join(os.environ.get("SNAP_DATA", "./"), "config.yaml")


# pylint: disable=E0213


class Config(BaseModel):
    """Hardware exporter configuration."""

    port: int = 10000
    level: str = "DEBUG"
    enable_collectors: List[str] = []

    @validator("port")
    def validate_port_range(cls, port: int) -> int:
        """Validate port range."""
        if not 1 <= port <= 65535:
            msg = "Port must be in [1, 65535]."
            logger.error(msg)
            raise ValueError(msg)
        return port

    @validator("level")
    def validate_level_choice(cls, level: str) -> str:
        """Validate logging level choice."""
        level = level.upper()
        choices = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level not in choices:
            msg = f"Level must be in {choices} (case-insensitive)."
            logger.error(msg)
            raise ValueError(msg)
        return level

    @validator("enable_collectors")
    def validate_enable_collector_choice(cls, enable_collectors: List[str]) -> List[str]:
        """Validate enable choice."""
        # We may need to update this set if collector.COLLECTOR_REGISTRIES is
        # changed.
        choices = {
            "collector.hpe_ssa",
            "collector.ipmi_dcmi",
            "collector.ipmi_sel",
            "collector.ipmi_sensor",
            "collector.lsi_sas_2",
            "collector.lsi_sas_3",
            "collector.mega_raid",
            "collector.poweredge_raid",
        }
        collectors = {collector.lower() for collector in enable_collectors}
        invalid_choices = collectors.difference(choices)
        if invalid_choices:
            msg = f"{collectors} must be in {choices} (case-insensitive)."
            logger.error(msg)
            raise ValueError(msg)
        return enable_collectors

    @classmethod
    def load_config(cls, config_file: str = DEFAULT_CONFIG) -> "Config":
        """Load configuration file and validate it."""
        if not os.path.exists(config_file):
            msg = f"Configuration file: {config_file} not exists."
            logger.error(msg)
            raise ValueError(msg)
        with open(config_file, "r", encoding="utf-8") as config:
            logger.info("Loaded exporter configuration: %s.", config_file)
            data = safe_load(config) or {}
            return cls(**data)
