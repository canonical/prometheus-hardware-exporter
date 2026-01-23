"""Module for hardware exporter related configuration."""

import os
import subprocess
from logging import getLogger
from typing import List, Optional

from pydantic import BaseModel, validator  # pylint: disable=no-name-in-module
from yaml import safe_load

logger = getLogger(__name__)

DEFAULT_CONFIG = os.path.join(os.environ.get("SNAP_DATA", "./"), "config.yaml")

DEFAULT_COLLECT_TIMEOUT = 30
DEFAULT_IPMI_SEL_INTERVAL = 86400 * 3  # 3 days
DEFAULT_IPMI_SEL_COLLECT_INTERVAL = 300
DEFAULT_REDFISH_CLIENT_TIMEOUT = 15
DEFAULT_REDFISH_CLIENT_MAX_RETRY = 1
DEFAULT_REDFISH_DISCOVER_CACHE_TTL = 86400
DEFAULT_IPMI_SEL_CACHE_TTL = 600


# pylint: disable=E0213


def get_bmc_address() -> Optional[str]:
    """Get BMC IP address by ipmitool."""
    cmd = "ipmitool lan print"
    try:
        output = subprocess.check_output(cmd.split(), text=True)
        for line in output.splitlines():
            values = line.split(":")
            if values[0].strip() == "IP Address":
                return values[1].strip()
    except subprocess.CalledProcessError:
        logger.debug("IPMI is not available")
    return None


class Config(BaseModel):
    """Hardware exporter configuration."""

    port: int = 10000
    level: str = "INFO"
    enable_collectors: List[str] = []

    collect_timeout: Optional[int] = DEFAULT_COLLECT_TIMEOUT
    ipmi_sel_interval: int = DEFAULT_IPMI_SEL_INTERVAL
    ipmi_sel_collect_interval: int = DEFAULT_IPMI_SEL_COLLECT_INTERVAL
    ipmi_sel_cache_ttl: int = DEFAULT_IPMI_SEL_CACHE_TTL

    hostname: str = ""
    username: str = ""
    password: str = ""
    driver_type: str = ""
    redfish_client_timeout: int = DEFAULT_REDFISH_CLIENT_TIMEOUT
    redfish_client_max_retry: int = DEFAULT_REDFISH_CLIENT_MAX_RETRY
    redfish_discover_cache_ttl: int = DEFAULT_REDFISH_DISCOVER_CACHE_TTL

    @validator("port")
    @classmethod
    def validate_port_range(cls, port: int) -> int:
        """Validate port range."""
        if not 1 <= port <= 65535:
            msg = "Port must be in [1, 65535]."
            logger.error(msg)
            raise ValueError(msg)
        return port

    @validator("level")
    @classmethod
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
    @classmethod
    def validate_enable_collector_choice(cls, enable_collectors: List[str]) -> List[str]:
        """Validate enable choice."""
        # We may need to update this set if COLLECTOR_REGISTRIES is
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
            "collector.redfish",
        }
        collectors = {collector.lower() for collector in enable_collectors}
        invalid_choices = collectors.difference(choices)
        if invalid_choices:
            msg = f"{collectors} must be in {choices} (case-insensitive)."
            logger.error(msg)
            raise ValueError(msg)
        return enable_collectors

    @validator("driver_type")
    @classmethod
    def validate_driver_type_choice(cls, driver_type: str) -> str:
        """Validate driver type choice."""
        driver = driver_type.upper()
        choices = {"LAN", "LAN_2_0", "KCS", "SSIF", "OPENIPMI", "SUNBMC", ""}
        if driver not in choices:
            msg = f"Driver type must be in {choices} (case-insensitive)."
            logger.error(msg)
            raise ValueError(msg)
        return driver_type

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
