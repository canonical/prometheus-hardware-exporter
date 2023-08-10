"""Redfish collector."""
from logging import getLogger
from typing import Any, Callable, Dict, List, Optional

import redfish
import redfish_utilities
from cachetools.func import ttl_cache
from redfish.rest.v1 import (
    HttpClient,
    InvalidCredentialsError,
    RetriesExhaustedError,
    SessionCreationError,
)

logger = getLogger(__name__)


# pylint: disable=too-many-arguments


class RedfishHelper:
    """Helper function for redfish."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        timeout: int,
        max_retry: int,
        discover_cache_ttl: int,
    ) -> None:
        """Initialize disover method with TTL value."""
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self.max_retry = max_retry
        self.discover = self.get_discover(discover_cache_ttl)

    def get_sensor_data(self) -> Dict[str, List]:
        """Get sensor data.

        Returns:
            sensor_data: a dictionary where key, value maps to chassis name, sensor data.
        """
        data = self._get_sensor_data()
        if not data:
            return {}
        output = {}
        for chassis in data:
            name = str(chassis["ChassisName"])
            sensors = []
            for sensor in chassis["Readings"]:
                reading: str = str(sensor["Reading"]) + (sensor["Units"] or "")

                sensors.append(
                    {
                        "Sensor": sensor["Name"],
                        "Reading": reading,
                        "Health": sensor["Health"] or "N/A",
                    }
                )
            output[name] = sensors
        return output

    def _get_sensor_data(self) -> Optional[List[Any]]:
        """Return sensor if sensor exists else None.

        Returns:
            sensors: List of dicts with details for each sensor
        """
        sensors: Optional[List[Any]] = None
        redfish_obj: Optional[HttpClient] = None
        try:
            redfish_obj = redfish.redfish_client(
                base_url=self.host,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                max_retry=self.max_retry,
            )
            redfish_obj.login(auth="session")
            sensors = redfish_utilities.get_sensors(redfish_obj)
            return sensors
        except (
            InvalidCredentialsError,
            SessionCreationError,
            ConnectionError,
            RetriesExhaustedError,
        ) as err:
            logger.exception(err)
        finally:
            # Log out
            if redfish_obj:
                redfish_obj.logout()
        return sensors

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
