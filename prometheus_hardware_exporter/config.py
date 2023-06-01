"""Module for hardware related configuration."""

import os
from logging import getLogger

from pydantic import BaseModel, validator
from yaml import safe_load

logger = getLogger(__name__)

DEFAULT_CONFIG = os.path.join(os.environ.get("SNAP_DATA", "./"), "config.yaml")


class Config(BaseModel):
    """Juju backup all configuration."""

    port: int = 10000
    level: str = "DEBUG"

    @validator("port")
    def validate_port_range(cls, port: int) -> int:  # noqa: N805 pylint: disable=E0213
        """Validate port range."""
        if not 1 <= port <= 65535:
            msg = "Port must be in [1, 65535]."
            logger.error(msg)
            raise ValueError(msg)
        return port

    @validator("level")
    def validate_level_choice(cls, level: str) -> str:  # noqa: N805 pylint: disable=E0213
        """Validate logging level choice."""
        level = level.upper()
        choices = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level not in choices:
            msg = f"Level must be in {choices} (case-insensitive)."
            logger.error(msg)
            raise ValueError(msg)
        return level

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
