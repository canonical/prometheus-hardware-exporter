"""IPMI Sensors metrics collector."""

from logging import getLogger
from typing import Dict, List

from ..utils import Command, ipmi_over_lan_args

logger = getLogger(__name__)


class IpmiMonitoring(Command):
    """Command line tool for getting ipmi sensors data."""

    prefix = ""
    command = "ipmimonitoring"

    def get_sensor_data(self, hostname: str) -> List[Dict[str, str]]:
        """Get sensor data.

        Returns:
            sensor_data: a list of dictionaries containing sensor data, or []
        """
        # --sdr-cache-recreate is required to automatically recreate the SDR cache in case it is
        # out of date or invalid. Without this, the service will stop getting sensor data if the
        # cache is out of date.
        args = "--sdr-cache-recreate " + ipmi_over_lan_args(self.config)
        result = self(args)
        if result.error:
            logger.error(result.error)
            return []

        raw_sensor_data = result.data.strip().split("\n")
        sensor_data = []
        sensor_data_fields = ["ID", "Name", "Type", "State", "Reading", "Units", "Event"]
        for sensor_data_item in raw_sensor_data[1:]:
            sensor_data_item_values = sensor_data_item.split("|")
            sensor_data_item_values = [entry.strip() for entry in sensor_data_item_values]
            sensor_data.append(dict(zip(sensor_data_fields, sensor_data_item_values)))
        return sensor_data
