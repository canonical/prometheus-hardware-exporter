"""Redfish collector."""
from logging import getLogger
from typing import Any, Dict, List, Optional

import redfish
import redfish_utilities
from cachetools import TTLCache, cached
from redfish.rest.v1 import (
    HttpClient,
    InvalidCredentialsError,
    RetriesExhaustedError,
    SessionCreationError,
)

logger = getLogger(__name__)

# timeout in seconds for initial connection
REDFISH_CLIENT_TIMEOUT = 3
# Number of times a request will retry after a timeout
REDFISH_CLIENT_MAX_RETRY = 1

# maximum size of cache before old items are removed
CACHE_MAXSIZE = 5
# how long should the cache be stored in seconds
CACHE_TTL = 86400


class RedfishHelper:
    """Helper function for redfish."""

    def get_sensor_data(self, host: str, username: str, password: str) -> Dict[str, List]:
        """Get sensor data.

        Returns:
            sensor_data: a dictionary where key, value maps to chassis name, sensor data.
        """
        data = self._get_sensor_data(host=host, username=username, password=password)
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

    def _get_sensor_data(self, host: str, username: str, password: str) -> Optional[List[Any]]:
        """Return sensor if sensor exists else None."""
        sensors: Optional[List[Any]] = None
        redfish_obj: Optional[HttpClient] = None
        try:
            redfish_obj = redfish.redfish_client(
                base_url=host,
                username=username,
                password=password,
                timeout=REDFISH_CLIENT_TIMEOUT,
                max_retry=REDFISH_CLIENT_MAX_RETRY,
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

    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TTL))
    def discover(self) -> bool:
        """Return true if redfish is been discovered."""
        logger.info("Discovering redfish services")
        services = redfish.discover_ssdp()
        if len(services) == 0:
            return False
        return True
