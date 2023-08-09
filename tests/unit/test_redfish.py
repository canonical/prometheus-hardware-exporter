import unittest
from time import sleep
from unittest.mock import Mock, patch

from redfish.rest.v1 import InvalidCredentialsError, SessionCreationError

from prometheus_hardware_exporter.collectors.redfish import RedfishHelper


class TestRedfishSensors(unittest.TestCase):
    """Test the RedfishSensors class."""

    def mock_helper(self):
        mock_ttl = 10
        return RedfishHelper(mock_ttl)

    def mock_redfish_client_args(self):
        host, username, password = "", "", ""
        mock_timeout = 3
        mock_max_retry = 1
        return host, username, password, mock_timeout, mock_max_retry

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
        helper = self.mock_helper()
        mock_args = self.mock_redfish_client_args()
        data = helper.get_sensor_data(*mock_args)
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
        helper = self.mock_helper()
        mock_args = self.mock_redfish_client_args()
        data = helper.get_sensor_data(*mock_args)
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
        helper = self.mock_helper()
        mock_args = self.mock_redfish_client_args()
        data = helper.get_sensor_data(*mock_args)
        self.assertEqual(data, {})

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_utilities")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish")
    def test_03__get_sensor_data_success(self, mock_redfish, mock_redfish_utilities):
        mock_redfish_utilities.get_sensors.return_value = ["return_data"]

        mock_redfish_client = Mock()
        mock_redfish.redfish_client.return_value = mock_redfish_client
        helper = self.mock_helper()
        mock_args = self.mock_redfish_client_args()
        data = helper._get_sensor_data(*mock_args)
        self.assertEqual(data, ["return_data"])
        mock_redfish_client.logout.assert_called()

    @patch("prometheus_hardware_exporter.collectors.redfish.logger")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_utilities")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish")
    def test_04__get_sensor_data_fail(self, mock_redfish, mock_redfish_utilities, mock_logger):
        mock_args = self.mock_redfish_client_args()
        for err in [InvalidCredentialsError(), SessionCreationError()]:
            mock_redfish_client = Mock()
            mock_redfish_client.login.side_effect = err
            mock_redfish.redfish_client.return_value = mock_redfish_client

            helper = self.mock_helper()
            helper._get_sensor_data(*mock_args)
            mock_redfish_client.logout.assert_called()
            mock_logger.exception.assert_called_with(mock_redfish_client.login.side_effect)

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish")
    def test_05__get_sensor_data_connection_error(self, mock_redfish):
        """Shouldn't raise error if connection fail."""
        mock_redfish.redfish_client.side_effect = ConnectionError()
        helper = self.mock_helper()
        mock_args = self.mock_redfish_client_args()
        helper._get_sensor_data(*mock_args)


class TestRedfishServiceStatus(unittest.TestCase):
    """Test the RedfishServiceStatus class."""

    def mock_helper(self):
        mock_ttl = 10
        return RedfishHelper(mock_ttl)

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
        ttl = 1
        helper = RedfishHelper(ttl)

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
