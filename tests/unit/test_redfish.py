import unittest
from unittest.mock import Mock, patch

from redfish.rest.v1 import InvalidCredentialsError, SessionCreationError

from prometheus_hardware_exporter.collectors.redfish import RedfishHelper


class TestRedfishSensors(unittest.TestCase):
    """Test the RedfishSensors class."""

    @patch.object(
        RedfishHelper,
        "_get_sensor_data",
        return_value=[
            {
                "ChassisName": 1,
                "Readings": [
                    {
                        "Name": "State",
                        "Reading": "Enabled",
                        "Units": None,
                        "State": "Enabled",
                        "Health": "OK",
                        "LowerFatal": None,
                        "LowerCritical": None,
                        "LowerCaution": None,
                        "UpperCaution": None,
                        "UpperCritical": None,
                        "UpperFatal": None,
                    },
                    {
                        "Name": "HpeServerPowerSupply State",
                        "Reading": "Enabled",
                        "Units": None,
                        "State": "Enabled",
                        "Health": "OK",
                        "LowerFatal": None,
                        "LowerCritical": None,
                        "LowerCaution": None,
                        "UpperCaution": None,
                        "UpperCritical": None,
                        "UpperFatal": None,
                    },
                    {
                        "Name": "HpeServerPowerSupply LineInputVoltage",
                        "Reading": 208,
                        "Units": "V",
                        "State": None,
                        "Health": None,
                        "LowerFatal": None,
                        "LowerCritical": None,
                        "LowerCaution": None,
                        "UpperCaution": None,
                        "UpperCritical": None,
                        "UpperFatal": None,
                    },
                    {
                        "Name": "HpeServerPowerSupply PowerCapacityWatts",
                        "Reading": 800,
                        "Units": "W",
                        "State": None,
                        "Health": None,
                        "LowerFatal": None,
                        "LowerCritical": None,
                        "LowerCaution": None,
                        "UpperCaution": None,
                        "UpperCritical": None,
                        "UpperFatal": None,
                    },
                ],
            }
        ],
    )
    def test_00_get_sensor_data_success(self, mock_get_sensor_data):
        helper = RedfishHelper()
        data = helper.get_sensor_data("", "", "")
        self.assertEqual(
            data,
            {
                "1": [
                    {"Sensor": "State", "Reading": "Enabled", "Health": "OK"},
                    {"Sensor": "HpeServerPowerSupply State", "Reading": "Enabled", "Health": "OK"},
                    {
                        "Sensor": "HpeServerPowerSupply LineInputVoltage",
                        "Reading": "208V",
                        "Health": "N/A",
                    },
                    {
                        "Sensor": "HpeServerPowerSupply PowerCapacityWatts",
                        "Reading": "800W",
                        "Health": "N/A",
                    },
                ]
            },
        )

    @patch.object(
        RedfishHelper,
        "_get_sensor_data",
        return_value=[
            {
                "ChassisName": 1,
                "Readings": [
                    {
                        "Name": "State",
                        "Reading": "Enabled",
                        "Units": None,
                        "State": "Enabled",
                        "Health": "OK",
                        "LowerFatal": None,
                        "LowerCritical": None,
                        "LowerCaution": None,
                        "UpperCaution": None,
                        "UpperCritical": None,
                        "UpperFatal": None,
                    },
                    {
                        "Name": "HpeServerPowerSupply State",
                        "Reading": "Enabled",
                        "Units": None,
                        "State": "Enabled",
                        "Health": "OK",
                        "LowerFatal": None,
                        "LowerCritical": None,
                        "LowerCaution": None,
                        "UpperCaution": None,
                        "UpperCritical": None,
                        "UpperFatal": None,
                    },
                ],
            },
            {
                "ChassisName": 2,
                "Readings": [
                    {
                        "Name": "HpeServerPowerSupply LineInputVoltage",
                        "Reading": 208,
                        "Units": "V",
                        "State": None,
                        "Health": None,
                        "LowerFatal": None,
                        "LowerCritical": None,
                        "LowerCaution": None,
                        "UpperCaution": None,
                        "UpperCritical": None,
                        "UpperFatal": None,
                    },
                    {
                        "Name": "HpeServerPowerSupply PowerCapacityWatts",
                        "Reading": 800,
                        "Units": "W",
                        "State": None,
                        "Health": None,
                        "LowerFatal": None,
                        "LowerCritical": None,
                        "LowerCaution": None,
                        "UpperCaution": None,
                        "UpperCritical": None,
                        "UpperFatal": None,
                    },
                ],
            },
        ],
    )
    def test_01_get_multiple_chassis_sensor_data_success(self, mock_get_sensor_data):
        helper = RedfishHelper()
        data = helper.get_sensor_data("", "", "")
        self.assertEqual(
            data,
            {
                "1": [
                    {"Sensor": "State", "Reading": "Enabled", "Health": "OK"},
                    {"Sensor": "HpeServerPowerSupply State", "Reading": "Enabled", "Health": "OK"},
                ],
                "2": [
                    {
                        "Sensor": "HpeServerPowerSupply LineInputVoltage",
                        "Reading": "208V",
                        "Health": "N/A",
                    },
                    {
                        "Sensor": "HpeServerPowerSupply PowerCapacityWatts",
                        "Reading": "800W",
                        "Health": "N/A",
                    },
                ],
            },
        )

    @patch.object(RedfishHelper, "_get_sensor_data", return_value=[])
    def test_02_get_sensor_data_fail(self, mock_get_sensor_data):
        helper = RedfishHelper()
        data = helper.get_sensor_data("", "", "")
        self.assertEqual(data, {})

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_utilities")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish")
    def test_03__get_sensor_data_success(self, mock_redfish, mock_redfish_utilities):
        mock_redfish_utilities.get_sensors.return_value = ["return_data"]

        mock_redfish_client = Mock()
        mock_redfish.redfish_client.return_value = mock_redfish_client
        helper = RedfishHelper()
        data = helper._get_sensor_data("", "", "")
        self.assertEqual(data, ["return_data"])
        mock_redfish_client.logout.assert_called()

    @patch("prometheus_hardware_exporter.collectors.redfish.logger")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_utilities")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish")
    def test_04__get_sensor_data_fail(self, mock_redfish, mock_redfish_utilities, mock_logger):
        for err in [InvalidCredentialsError(), SessionCreationError()]:
            mock_redfish_utilities.get_sensors.side_effect = err

            mock_redfish_client = Mock()
            mock_redfish.redfish_client.return_value = mock_redfish_client

            helper = RedfishHelper()
            data = helper._get_sensor_data("", "", "")
            self.assertEqual(data, None)
            mock_redfish_client.logout.assert_called()
            mock_logger.exception.assert_called_with(
                mock_redfish_utilities.get_sensors.side_effect
            )


class TestRedfishServiceStatus(unittest.TestCase):
    """Test the RedfishServiceStatus class."""

    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish.discover_ssdp",
        return_value=[1, 2, 3],
    )
    def test_00_get_service_status_good(self, mock_discover_ssdp):
        helper = RedfishHelper()
        ok = helper.discover()
        self.assertEqual(ok, True)

    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish.discover_ssdp", return_value=[]
    )
    def test_01_get_service_status_bad(self, mock_call):
        helper = RedfishHelper()
        ok = helper.discover()
        self.assertEqual(ok, False)
