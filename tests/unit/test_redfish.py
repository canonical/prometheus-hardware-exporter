import unittest
from unittest.mock import patch

from test_resources.redfish.redfish_sample_data import (
    SAMPLE_RF_DISCOVER_OUTPUT,
    SAMPLE_RF_SENSOR_DATA,
)

from prometheus_hardware_exporter.collectors.redfish import (
    RedfishSensors,
    RedfishServiceStatus,
)
from prometheus_hardware_exporter.utils import Command, Result

SAMPLE_RF_SENSORS_OUTPUT = "tests/unit/test_resources/redfish/redfish_sensors_sample_output.txt"


class TestRedfishSensors(unittest.TestCase):
    """Test the RedfishSensors class."""

    @patch.object(Command, "__call__")
    def test_00_get_sensor_data_success(self, mock_call):
        with open(SAMPLE_RF_SENSORS_OUTPUT, "r") as content:
            mock_call.return_value = Result(content.read(), None)
            rf_sensors = RedfishSensors()
            sensor_data = rf_sensors.get_sensor_data("username", "password", "localhost")
            self.assertEqual(sensor_data, SAMPLE_RF_SENSOR_DATA)

    @patch.object(Command, "__call__")
    def test_01_get_sensor_data_error(self, mock_call):
        mock_call.return_value = Result("", True)
        rf_sensors = RedfishSensors()
        sensor_data = rf_sensors.get_sensor_data("username", "password", "localhost")
        self.assertEqual(sensor_data, {})


class TestRedfishServiceStatus(unittest.TestCase):
    """Test the RedfishServiceStatus class."""

    @patch.object(Command, "__call__")
    def test_00_get_service_status_good(self, mock_call):
        mock_call.return_value = Result(SAMPLE_RF_DISCOVER_OUTPUT, None)
        rf_discover = RedfishServiceStatus()
        rf_status = rf_discover.get_service_status()
        self.assertEqual(rf_status, True)

    @patch.object(Command, "__call__")
    def test_01_get_service_status_bad(self, mock_call):
        mock_call.return_value = Result("No Redfish services discovered\n", None)
        rf_discover = RedfishServiceStatus()
        rf_status = rf_discover.get_service_status()
        self.assertEqual(rf_status, False)

    @patch.object(Command, "__call__")
    def test_02_get_service_status_error(self, mock_call):
        mock_call.return_value = Result("", True)
        rf_discover = RedfishServiceStatus()
        rf_status = rf_discover.get_service_status()
        self.assertEqual(rf_status, False)
