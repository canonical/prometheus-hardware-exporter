import unittest
from time import sleep
from unittest.mock import Mock, patch

from redfish.rest.v1 import InvalidCredentialsError, SessionCreationError

from prometheus_hardware_exporter.collectors.redfish import RedfishHelper
from prometheus_hardware_exporter.config import Config


class TestRedfishSensors(unittest.TestCase):
    """Test the RedfishSensors class."""

    def mock_helper(self):
        mock_config = Mock()
        return RedfishHelper(mock_config)

    @patch.object(
        RedfishHelper,
        "_retrieve_redfish_sensor_data",
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
    def test_00_get_sensor_data_success(self, mock_sensor_data):
        helper = self.mock_helper()
        data = helper.get_sensor_data()
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
        "_retrieve_redfish_sensor_data",
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
    def test_01_get_multiple_chassis_sensor_data_success(self, mock_sensor_data):
        helper = self.mock_helper()
        data = helper.get_sensor_data()
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

    @patch.object(RedfishHelper, "_retrieve_redfish_sensor_data", return_value=[])
    def test_02_get_sensor_data_fail(self, mock_sensor_data):
        helper = self.mock_helper()
        data = helper.get_sensor_data()
        self.assertEqual(data, {})

    def test_03_map_sensor_data_to_chassis(self):
        mock_data = [
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
        ]

        helper = self.mock_helper()
        output = helper._map_sensor_data_to_chassis(mock_data)
        self.assertEqual(
            output,
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

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_utilities.get_sensors")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    def test_04_retrieve_redfish_sensor_data_success(self, mock_redfish_client, mock_get_sensors):
        mock_get_sensors.return_value = ["return_data"]

        mock_redfish_obj = Mock()
        mock_redfish_client.return_value.__enter__.return_value = mock_redfish_obj
        helper = self.mock_helper()
        data = helper._retrieve_redfish_sensor_data()
        self.assertEqual(data, ["return_data"])

    @patch("prometheus_hardware_exporter.collectors.redfish.logger")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_utilities")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    def test_05_retrieve_redfish_sensor_data_fail(
        self, mock_redfish_client, mock_redfish_utilities, mock_logger
    ):
        for err in [InvalidCredentialsError(), SessionCreationError()]:
            mock_redfish_client.return_value.__enter__.side_effect = err

            helper = self.mock_helper()
            data = helper._retrieve_redfish_sensor_data()
            mock_logger.exception.assert_called_with(
                mock_redfish_client.return_value.__enter__.side_effect
            )
            self.assertEqual(data, [])

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    def test_06_retrieve_redfish_sensor_data_connection_error(self, mock_redfish_client):
        """Shouldn't raise error if connection fail."""
        mock_redfish_client.return_value.__enter__.side_effect = ConnectionError()
        helper = self.mock_helper()
        data = helper._retrieve_redfish_sensor_data()
        self.assertEqual(data, [])


class TestRedfishServiceStatus(unittest.TestCase):
    """Test the RedfishServiceStatus class."""

    def mock_helper(self):
        mock_ttl = 10
        mock_timeout = 3
        mock_max_retry = 1
        mock_config = Config(
            redfish_host="",
            redfish_username="",
            redfish_password="",
            redfish_client_timeout=mock_timeout,
            redfish_client_max_retry=mock_max_retry,
            redfish_discover_cache_ttl=mock_ttl,
        )
        return RedfishHelper(mock_config)

    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish.discover_ssdp",
        return_value=[1, 2, 3],
    )
    def test_00_get_service_status_good(self, mock_discover_ssdp):
        helper = self.mock_helper()
        ok = helper.discover()
        self.assertEqual(ok, True)

    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish.discover_ssdp", return_value=[]
    )
    def test_01_get_service_status_bad(self, mock_call):
        helper = self.mock_helper()
        ok = helper.discover()
        self.assertEqual(ok, False)

    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish.discover_ssdp",
        return_value=[1, 2, 3],
    )
    def test_02_discover_cache(self, mock_discover):
        mock_timeout = 3
        mock_max_retry = 1
        ttl = 1
        mock_config = Config(
            redfish_host="",
            redfish_username="",
            redfish_password="",
            redfish_client_timeout=mock_timeout,
            redfish_client_max_retry=mock_max_retry,
            redfish_discover_cache_ttl=ttl,
        )
        helper = RedfishHelper(mock_config)

        output = helper.discover()
        self.assertEqual(output, True)
        mock_discover.assert_called()
        mock_discover.reset_mock()

        # output from cache
        output = helper.discover()
        self.assertEqual(output, True)
        mock_discover.assert_not_called()

        # wait till cache expires
        sleep(ttl + 1)
        output = helper.discover()
        self.assertEqual(output, True)
        mock_discover.assert_called()
