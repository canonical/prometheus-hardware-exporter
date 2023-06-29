"""Redfish collector."""

from logging import getLogger
from typing import Dict, List

from ..utils import Command

logger = getLogger(__name__)


class RedfishSensors(Command):
    """Command line tool for getting sensor data using redfish."""

    prefix = ""
    command = "rf_sensor_list.py"

    def get_sensor_data(self, username: str, password: str, rhost: str) -> Dict[str, List]:
        """Get sensor data.

        Returns:
            sensor_data: a dictionary where key, value maps to chassis name, sensor data.
        """
        result = self(f"-u {username} -p {password} -r {rhost}")
        if result.error:
            logger.error(result.error)
            return {}

        raw_sensor_data = result.data.strip().split("\n")
        sensor_data = {}
        sensor_data_fields = ["Sensor", "Reading", "Health", "LF", "LC", "LNC", "UNC", "UC", "UF"]
        curr_chassis_name = ""
        curr_chassis_data: List[Dict] = []
        for line in raw_sensor_data:
            line = line.strip()
            if line.startswith("Chassis ") and line.endswith(" Status"):
                curr_chassis_name = line[9:][:-8]
                curr_chassis_data = []
                continue
            curr_sensor_data = line.split("|")
            if len(curr_sensor_data) != 9:
                logger.warning("Ignored line in redfish sensor output: %s", line)
                continue
            sensor_data_item = [entry.strip() for entry in curr_sensor_data]
            sensor_data_map = dict(zip(sensor_data_fields, sensor_data_item))
            if any((k != v) for k, v in sensor_data_map.items()):
                curr_chassis_data.append(sensor_data_map)
                sensor_data[curr_chassis_name] = curr_chassis_data

        return sensor_data


class RedfishServiceStatus(Command):
    """Command line tool for getting redfish service status."""

    prefix = ""
    command = "rf_discover.py"

    def get_service_status(self) -> bool:
        """Return whether redfish service is available or not."""
        result = self()
        if result.error:
            logger.error(result.error)
            return False

        rf_services = result.data.strip()
        return "No Redfish services discovered" not in rf_services
