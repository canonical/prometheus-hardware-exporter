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
        mock_redfish_client.return_value = mock_redfish_obj
        helper = self.mock_helper()
        data = helper._retrieve_redfish_sensor_data()
        self.assertEqual(data, ["return_data"])
        mock_redfish_client.return_value.logout.assert_called()

    @patch("prometheus_hardware_exporter.collectors.redfish.logger")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_utilities")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    def test_05_retrieve_redfish_sensor_data_fail(
        self, mock_redfish_client, mock_redfish_utilities, mock_logger
    ):
        for err in [InvalidCredentialsError(), SessionCreationError()]:
            mock_redfish_obj = Mock()
            mock_redfish_client.return_value = mock_redfish_obj
            mock_redfish_client.return_value.login.side_effect = err

            helper = self.mock_helper()
            data = helper._retrieve_redfish_sensor_data()
            mock_logger.exception.assert_called_with(
                mock_redfish_client.return_value.login.side_effect
            )
            mock_redfish_client.return_value.logout.assert_called()

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    def test_06_retrieve_redfish_sensor_data_connection_error(self, mock_redfish_client):
        """Shouldn't raise error if connection fail."""
        mock_redfish_client.side_effect = ConnectionError()
        helper = self.mock_helper()
        data = helper._retrieve_redfish_sensor_data()
        self.assertEqual(data, [])

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_07_get_processor_data_success(self, mock_get_system_ids, mock_redfish_client):
        mock_redfish_obj = Mock()
        mock_system_ids = ["s1", "s2"]
        mock_get_system_ids.return_value = mock_system_ids
        mock_redfish_client.return_value = mock_redfish_obj

        def mock_get_response(uri):
            response = Mock()
            if "Systems/s1/Processors/p11" in uri:
                response.dict = {
                    "Id": "p11",
                    "Model": "Processor s1 Model 1",
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            elif "Systems/s1/Processors/p12" in uri:
                response.dict = {
                    "Id": "p12",
                    "Model": "Processor s1 Model 2",
                    "Status": {"Health": "Warning", "State": "Disabled"},
                }
            elif "Systems/s2/Processors/p21" in uri:
                response.dict = {
                    "Id": "p21",
                    "Model": "Processor s2 Model 1",
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            elif "Systems/s1/Processors" in uri:
                response.dict = {
                    "Members": [
                        {"@odata.id": "/redfish/v1/Systems/s1/Processors/p11"},
                        {"@odata.id": "/redfish/v1/Systems/s1/Processors/p12"},
                    ]
                }
            elif "Systems/s2/Processors" in uri:
                response.dict = {
                    "Members": [
                        {"@odata.id": "/redfish/v1/Systems/s2/Processors/p21"},
                    ]
                }
            return response

        mock_redfish_obj.get.side_effect = mock_get_response

        helper = self.mock_helper()
        processor_count, processor_data = helper.get_processor_data()

        self.assertEqual(processor_count, {"s1": 2, "s2": 1})
        self.assertEqual(
            processor_data,
            {
                "s1": [
                    {
                        "processor_id": "p11",
                        "model": "Processor s1 Model 1",
                        "health": "OK",
                        "state": "Enabled",
                    },
                    {
                        "processor_id": "p12",
                        "model": "Processor s1 Model 2",
                        "health": "Warning",
                        "state": "Disabled",
                    },
                ],
                "s2": [
                    {
                        "processor_id": "p21",
                        "model": "Processor s2 Model 1",
                        "health": "OK",
                        "state": "Enabled",
                    },
                ],
            },
        )

        mock_get_system_ids.assert_called_once_with(mock_redfish_obj)

        mock_redfish_obj.get.assert_any_call("/redfish/v1/Systems/s1/Processors")
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Systems/s1/Processors/p11")
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Systems/s1/Processors/p12")
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Systems/s2/Processors/p21")
        mock_redfish_obj.logout.assert_called_once()

    def test_08_get_processor_data_fail(self):
        pass

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.collections.get_collection_ids"
    )
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_09_get_storage_controller_data_success(
        self, mock_get_system_ids, mock_get_collection_ids, mock_redfish_client
    ):
        mock_redfish_obj = Mock()
        mock_system_ids = ["s1"]
        mock_storage_ids = ["STOR1", "STOR2"]

        mock_get_system_ids.return_value = mock_system_ids
        mock_redfish_client.return_value = mock_redfish_obj
        mock_get_collection_ids.return_value = mock_storage_ids

        def mock_get_response(uri):
            response = Mock()
            if "Systems/s1/Storage/STOR1" in uri:
                response.dict = {
                    "StorageControllers": [
                        {
                            "MemberId": "sc0",
                            "Status": {"Health": "OK", "State": "Enabled"},
                        }
                    ]
                }
            elif "Systems/s1/Storage/STOR2" in uri:
                response.dict = {
                    "StorageControllers": [
                        {
                            "MemberId": "sc1",
                            "Status": {"Health": "OK", "State": "Enabled"},
                        }
                    ]
                }
            return response

        mock_redfish_obj.get.side_effect = mock_get_response

        helper = self.mock_helper()
        storage_controller_count, storage_controller_data = helper.get_storage_controller_data()

        self.assertEqual(storage_controller_count, {"s1": 2})
        self.assertEqual(
            storage_controller_data,
            {
                "s1": [
                    {
                        "storage_id": "STOR1",
                        "controller_id": "sc0",
                        "health": "OK",
                        "state": "Enabled",
                    },
                    {
                        "storage_id": "STOR2",
                        "controller_id": "sc1",
                        "health": "OK",
                        "state": "Enabled",
                    },
                ],
            },
        )

        mock_get_system_ids.assert_called_once_with(mock_redfish_obj)

        mock_redfish_obj.get.assert_any_call("/redfish/v1/Systems/s1/Storage/STOR1")
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Systems/s1/Storage/STOR2")
        mock_redfish_obj.logout.assert_called_once()

    def test_10_get_storage_controller_data_fail(self):
        pass

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"
    )
    def test_11_get_network_adapter_data_success(self, mock_get_chassis_ids, mock_redfish_client):
        mock_redfish_obj = Mock()
        mock_chassis_ids = ["c1", "c2"]
        mock_get_chassis_ids.return_value = mock_chassis_ids
        mock_redfish_client.return_value = mock_redfish_obj

        def mock_get_response(uri):
            response = Mock()
            response.status = 200
            if "/Chassis/c1/NetworkAdapters" in uri:
                response.dict = {
                    "Members": [
                        {"@odata.id": "/redfish/v1/Chassis/c1/NetworkAdapters/NetAdap11"},
                        {"@odata.id": "/redfish/v1/Chassis/c1/NetworkAdapters/NetAdap12"},
                    ]
                }

            elif "/Chassis/c2/NetworkAdapters" in uri:
                response.dict = {
                    "Members": [
                        {"@odata.id": "/redfish/v1/Chassis/c2/NetworkAdapters/NetAdap21"},
                    ]
                }

            return response

        mock_redfish_obj.get.side_effect = mock_get_response

        helper = self.mock_helper()
        network_adapter_count = helper.get_network_adapter_data()

        self.assertEqual(network_adapter_count, {"c1": 2, "c2": 1})
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Chassis/c1/NetworkAdapters")
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Chassis/c2/NetworkAdapters")
        mock_redfish_obj.logout.assert_called_once()

    def test_12_get_network_adapter_data_fail(self):
        pass

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"
    )
    def test_13_get_chassis_data_success(self, mock_get_chassis_ids, mock_redfish_client):
        mock_chassis_ids = ["c1", "c2"]
        mock_redfish_obj = Mock()
        mock_get_chassis_ids.return_value = mock_chassis_ids
        mock_redfish_client.return_value = mock_redfish_obj

        def mock_get_response(uri):
            response = Mock()
            if "/Chassis/c1" in uri:
                response.dict = {
                    "Id": "c1",
                    "ChassisType": "RackMount",
                    "Manufacturer": "",
                    "Model": "Chassis Model c1",
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            elif "/Chassis/c2" in uri:
                response.dict = {
                    "Id": "c2",
                    "ChassisType": "RackMount",
                    "Manufacturer": "",
                    "Model": "Chassis Model c2",
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            return response

        mock_redfish_obj.get.side_effect = mock_get_response

        helper = self.mock_helper()
        chassis_data = helper.get_chassis_data()

        self.assertEqual(
            chassis_data,
            {
                "c1": {
                    "chassis_id": "c1",
                    "chassis_type": "RackMount",
                    "manufacturer": "",
                    "model": "Chassis Model c1",
                    "health": "OK",
                    "state": "Enabled",
                },
                "c2": {
                    "chassis_id": "c2",
                    "chassis_type": "RackMount",
                    "manufacturer": "",
                    "model": "Chassis Model c2",
                    "health": "OK",
                    "state": "Enabled",
                },
            },
        )
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Chassis/c1")
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Chassis/c2")
        mock_redfish_obj.logout.assert_called_once()

    def test_14_get_chassis_data_fail(self):
        pass

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.collections.get_collection_ids"
    )
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_15_get_storage_drive_data_success(
        self, mock_get_system_ids, mock_get_collection_ids, mock_redfish_client
    ):
        mock_redfish_obj = Mock()
        mock_system_ids = ["s1"]
        mock_storage_ids = ["STOR1", "STOR2"]

        mock_get_system_ids.return_value = mock_system_ids
        mock_redfish_client.return_value = mock_redfish_obj
        mock_get_collection_ids.return_value = mock_storage_ids

        def mock_get_response(uri):
            response = Mock()
            if "Systems/s1/Storage/STOR1/Drives/d11" in uri:
                response.dict = {
                    "Id": "d11",
                    "Status": {"Health": "OK", "State": "Enabled"},
                }

            elif "Systems/s1/Storage/STOR1/Drives/d12" in uri:
                response.dict = {
                    "Id": "d12",
                    "Status": {"Health": "OK", "State": "Disabled"},
                }

            elif "Systems/s1/Storage/STOR2/Drives/d21" in uri:
                response.dict = {
                    "Id": "d21",
                    "Status": {"Health": None, "State": "Enabled"},
                }
            elif "Systems/s1/Storage/STOR1" in uri:
                response.dict = {
                    "Drives": [
                        {"@odata.id": "/redfish/v1/Systems/s1/Storage/STOR1/Drives/d11"},
                        {"@odata.id": "/redfish/v1/Systems/s1/Storage/STOR1/Drives/d12"},
                    ]
                }
            elif "Systems/s1/Storage/STOR2" in uri:
                response.dict = {
                    "Drives": [
                        {"@odata.id": "/redfish/v1/Systems/s1/Storage/STOR2/Drives/d21"},
                    ]
                }
            return response

        mock_redfish_obj.get.side_effect = mock_get_response

        helper = self.mock_helper()
        storage_drive_count, storage_drive_data = helper.get_storage_drive_data()

        self.assertEqual(storage_drive_count, {"s1": 3})
        self.assertEqual(
            storage_drive_data,
            {
                "s1": [
                    {
                        "storage_id": "STOR1",
                        "drive_id": "d11",
                        "health": "OK",
                        "state": "Enabled",
                    },
                    {
                        "storage_id": "STOR1",
                        "drive_id": "d12",
                        "health": "OK",
                        "state": "Disabled",
                    },
                    {
                        "storage_id": "STOR2",
                        "drive_id": "d21",
                        "health": "NA",
                        "state": "Enabled",
                    },
                ],
            },
        )

        mock_get_system_ids.assert_called_once_with(mock_redfish_obj)

        mock_redfish_obj.get.assert_any_call("/redfish/v1/Systems/s1/Storage/STOR1")
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Systems/s1/Storage/STOR1/Drives/d11")
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Systems/s1/Storage/STOR1/Drives/d12")
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Systems/s1/Storage/STOR2")
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Systems/s1/Storage/STOR2/Drives/d21")
        mock_redfish_obj.logout.assert_called_once()


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
