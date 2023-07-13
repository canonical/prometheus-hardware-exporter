"""Redfish collector."""
from logging import getLogger
from typing import Any, Dict, List, Optional

import redfish
import redfish_utilities
from redfish.rest.v1 import HttpClient, InvalidCredentialsError, SessionCreationError

logger = getLogger(__name__)


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
                base_url=host, username=username, password=password
            )
            redfish_obj.login(auth="session")
            sensors = redfish_utilities.get_sensors(redfish_obj)
            return sensors
        except (InvalidCredentialsError, SessionCreationError, ConnectionError) as err:
            logger.exception(err)
        finally:
            # Log out
            if redfish_obj:
                redfish_obj.logout()
        return sensors

    def discover(self) -> bool:
        """Return true if redfish is been discovered."""
        services = redfish.discover_ssdp()
        if len(services) == 0:
            return False
        return True
