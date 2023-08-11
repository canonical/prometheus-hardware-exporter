"""Redfish collector."""
from logging import getLogger
from typing import Any, Callable, Dict, List

import redfish
import redfish_utilities
from cachetools.func import ttl_cache
from redfish.rest.v1 import (
    InvalidCredentialsError,
    RetriesExhaustedError,
    SessionCreationError,
)

from prometheus_hardware_exporter.config import Config

logger = getLogger(__name__)


class RedfishHelper:
    """Helper function for redfish."""

    def __init__(self, config: Config) -> None:
        """Initialize redfish login args and cache TTL value for discover method."""
        self.host = config.redfish_host
        self.username = config.redfish_username
        self.password = config.redfish_password
        self.timeout = config.redfish_client_timeout
        self.max_retry = config.redfish_client_max_retry
        self.discover = self.get_discover(config.redfish_discover_cache_ttl)

    def get_sensor_data(self) -> Dict[str, List]:
        """Get sensor data.

        Returns:
            sensor_data: a dictionary where key, value maps to chassis name, sensor data.
        """
        data = self._retrieve_redfish_sensor_data()
        return self._map_sensor_data_to_chassis(data)

    def _map_sensor_data_to_chassis(self, sensor_data: List[Any]) -> Dict[str, List]:
        output = {}
        for chassis in sensor_data:
            output[str(chassis["ChassisName"])] = [
                {
                    "Sensor": sensor["Name"],
                    "Reading": str(sensor["Reading"]) + (sensor["Units"] or ""),
                    "Health": sensor["Health"] or "N/A",
                }
                for sensor in chassis["Readings"]
            ]
        return output

    def _retrieve_redfish_sensor_data(self) -> List[Any]:
        """Return sensor if sensor exists else None.

        Returns:
            sensors: List of dicts with details for each sensor
        """
        try:
            with redfish.redfish_client(
                base_url=self.host,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                max_retry=self.max_retry,
            ) as redfish_obj:
                return redfish_utilities.get_sensors(redfish_obj)
        except (
            InvalidCredentialsError,
            SessionCreationError,
            ConnectionError,
            RetriesExhaustedError,
        ) as err:
            logger.exception(err)
        return []

    def get_discover(self, ttl: int) -> Callable:
        """Return the cached discover function.

        Passes the ttl value to the cache decorator at runtime.
        """

        @ttl_cache(ttl=ttl)
        def _discover() -> bool:
            """Return true if redfish services have been discovered."""
            logger.info("Discovering redfish services...")
            services = redfish.discover_ssdp()
            if len(services) == 0:
                logger.info("No redfish services discovered")
                return False
            logger.info("Discovered redfish services: %s", services)
            return True

        return _discover
