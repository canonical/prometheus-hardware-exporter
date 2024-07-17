import unittest
from time import sleep
from unittest.mock import Mock, patch

import redfish_utilities
from parameterized import parameterized
from redfish.rest.v1 import (
    BadRequestError,
    InvalidCredentialsError,
    RetriesExhaustedError,
    SessionCreationError,
)

from prometheus_hardware_exporter.collectors.redfish import RedfishHelper


class TestRedfishMetrics(unittest.TestCase):
    """Test metrics methods in RedfishHelper."""

    def setUp(self):
        redfish_client_patcher = patch(
            "prometheus_hardware_exporter.collectors.redfish.redfish_client"
        )
        self.mock_redfish_client = redfish_client_patcher.start()
        self.addCleanup(redfish_client_patcher.stop)

    def test_verify_redfish_call_success(self):
        uri = "/some/test/uri"
        mock_response = Mock()
        mock_response.status = 200
        mock_response.dict = {"foo": 1, "bar": 2}
        mock_redfish_obj = Mock()
        mock_redfish_obj.get.return_value = mock_response
        self.mock_redfish_client.return_value = mock_redfish_obj

        redfish_helper = RedfishHelper(Mock())
        with RedfishHelper(Mock()) as redfish_helper:
            resp_dict = redfish_helper._verify_redfish_call(uri)

        self.assertEqual(resp_dict, {"foo": 1, "bar": 2})
        mock_redfish_obj.get.assert_called_with(uri)

    @patch("prometheus_hardware_exporter.collectors.redfish.logger")
    def test_verify_redfish_call_fail(self, mock_logger):
        uri = "/some/test/uri"
        mock_response = Mock()
        mock_response.status = 401
        mock_redfish_obj = Mock()
        mock_redfish_obj.get.return_value = mock_response
        self.mock_redfish_client.return_value = mock_redfish_obj

        with RedfishHelper(Mock()) as redfish_helper:
            resp_dict = redfish_helper._verify_redfish_call(uri)

        mock_redfish_obj.get.assert_called_with(uri)
        self.assertIsNone(resp_dict)

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
    def test_get_sensor_data_success(self, mock_sensor_data):
        with RedfishHelper(Mock()) as redfish_helper:
            data = redfish_helper.get_sensor_data()
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
    def test_get_multiple_chassis_sensor_data_success(self, mock_sensor_data):
        with RedfishHelper(Mock()) as redfish_helper:
            data = redfish_helper.get_sensor_data()
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
    def test_get_sensor_data_fail(self, mock_sensor_data):
        with RedfishHelper(Mock()) as redfish_helper:
            data = redfish_helper.get_sensor_data()
        self.assertEqual(data, {})

    def test_map_sensor_data_to_chassis(self):
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

        with RedfishHelper(Mock()) as redfish_helper:
            output = redfish_helper._map_sensor_data_to_chassis(mock_data)
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
    def test_retrieve_redfish_sensor_data_success(self, mock_get_sensors):
        mock_get_sensors.return_value = ["return_data"]

        mock_redfish_obj = Mock()
        self.mock_redfish_client.return_value = mock_redfish_obj
        with RedfishHelper(Mock()) as redfish_helper:
            data = redfish_helper._retrieve_redfish_sensor_data()
        self.assertEqual(data, ["return_data"])

    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_get_processor_data_success(self, mock_get_system_ids):
        mock_redfish_obj = Mock()
        mock_system_ids = ["s1", "s2"]
        mock_get_system_ids.return_value = mock_system_ids
        self.mock_redfish_client.return_value = mock_redfish_obj

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
                    "Status": {"Health": "NotOK", "State": "Disabled"},
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

        with RedfishHelper(Mock()) as redfish_helper:
            processor_count, processor_data = redfish_helper.get_processor_data()

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
                        "health": "NotOK",
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

    def test__storage_root_uri(self):
        """Test RedfishHelper._storage_root_uri method."""
        for storage_name in ["Storage", "Storages", "TestStorage"]:
            expected_uri = f"/redfish/v1/Systems/S1/{storage_name}/"
            uri = RedfishHelper._storage_root_uri("S1", storage_name)
            assert uri == expected_uri

    @parameterized.expand(["Storage", "Storages"])
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.collections.get_collection_ids"  # noqa: E501
    )
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_get_storage_controller_data_success(
        self, storage_name, mock_get_system_ids, mock_get_collection_ids
    ):
        mock_system_ids = ["s1"]
        mock_storage_ids = ["STOR1", "STOR2", "STOR3", "STOR4"]

        mock_get_system_ids.return_value = mock_system_ids
        mock_get_collection_ids.return_value = mock_storage_ids

        def mock_get_response(uri):
            response = Mock()
            storage_root = f"Systems/s1/{storage_name}"
            if f"{storage_root}/STOR1" in uri:
                response.dict = {
                    "StorageControllers": [
                        {
                            "MemberId": "sc0",
                            "Status": {"Health": "OK", "State": "Enabled"},
                        }
                    ]
                }
            elif f"{storage_root}/STOR2" in uri:
                response.dict = {
                    "StorageControllers": [
                        {
                            "MemberId": "sc1",
                            "Status": {"Health": "OK", "State": "Enabled"},
                        }
                    ]
                }
            elif f"{storage_root}/STOR3" in uri:  # missing Health case
                response.dict = {
                    "StorageControllers": [
                        {
                            "MemberId": "sc2",
                            "Status": {"State": "Enabled"},
                        }
                    ]
                }
            elif f"{storage_root}/STOR4" in uri:  # Health is None
                response.dict = {
                    "StorageControllers": [
                        {
                            "MemberId": "sc3",
                            "Status": {"Health": None, "State": "Enabled"},
                        }
                    ]
                }
            # response for GET request to /redfish/v1/Systems/<sys_id>/
            elif "Systems" in uri:
                response.dict = {
                    "Storage": {"@odata.id": f"/redfish/v1/Systems/sX/{storage_name}"}
                }
            return response

        mock_redfish_obj = Mock()
        mock_redfish_obj.get.side_effect = mock_get_response
        self.mock_redfish_client.return_value = mock_redfish_obj

        with RedfishHelper(Mock()) as redfish_helper:
            (
                storage_controller_count,
                storage_controller_data,
            ) = redfish_helper.get_storage_controller_data()

        self.assertEqual(storage_controller_count, {"s1": 4})
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
                    {
                        "storage_id": "STOR3",
                        "controller_id": "sc2",
                        "health": "NA",
                        "state": "Enabled",
                    },
                    {
                        "storage_id": "STOR4",
                        "controller_id": "sc3",
                        "health": "NA",
                        "state": "Enabled",
                    },
                ],
            },
        )

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.collections.get_collection_ids"  # noqa: E501
    )
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_get_storage_controller_data_success_with_non_standard_api(
        self, mock_get_system_ids, mock_get_collection_ids, mock_redfish_client
    ):
        mock_redfish_obj = Mock()
        mock_system_ids = ["s1"]
        mock_storage_ids = ["STOR1", "STOR2", "STOR3"]

        mock_get_system_ids.return_value = mock_system_ids
        mock_redfish_client.return_value = mock_redfish_obj
        mock_get_collection_ids.return_value = mock_storage_ids

        def mock_get_response(uri):
            response = Mock()
            if uri.endswith("Systems/s1/Storage/STOR1"):
                response.dict = {
                    "Controllers": {
                        "@odata.id": "/redfish/v1/Systems/s1/Storage/STOR1/Controllers"
                    }
                }
            elif uri.endswith("Systems/s1/Storage/STOR2"):
                response.dict = {
                    "Controllers": {
                        "@odata.id": "/redfish/v1/Systems/s1/Storage/STOR2/Controllers"
                    }
                }
            # response for non-standard api response
            elif uri.endswith("Systems/s1/Storage/STOR3"):
                response.dict = {"UnknownKey": {}}
            elif uri.endswith("Systems/s1/Storage/STOR1/Controllers"):
                response.dict = {
                    "Members": [
                        {"@odata.id": "/redfish/v1/Systems/s1/Storage/STOR1/Controllers/sc0"}
                    ]
                }
            elif uri.endswith("Systems/s1/Storage/STOR2/Controllers"):
                response.dict = {
                    "Members": [
                        {"@odata.id": "/redfish/v1/Systems/s1/Storage/STOR2/Controllers/sc1"},
                        {"@odata.id": "/redfish/v1/Systems/s1/Storage/STOR2/Controllers/sc2"},
                    ]
                }
            elif uri.endswith("Systems/s1/Storage/STOR1/Controllers/sc0"):
                response.dict = {
                    "Status": {
                        "State": "Enabled",
                        "Health": "OK",
                    },
                    "Id": "sc0",
                }
            elif uri.endswith("Systems/s1/Storage/STOR2/Controllers/sc1"):
                response.dict = {
                    "Status": {
                        "State": "Enabled",
                        "Health": "OK",
                    },
                    "Id": "sc1",
                }
            # response for non-valid response
            elif uri.endswith("Systems/s1/Storage/STOR2/Controllers/sc2"):
                response.dict = {}
            # response for GET request to /redfish/v1/Systems/<sys_id>/
            elif "Systems" in uri:
                response.dict = {"Storage": {"@odata.id": "/redfish/v1/Systems/sX/Storage"}}
            return response

        mock_redfish_obj.get.side_effect = mock_get_response

        with RedfishHelper(Mock()) as helper:
            (
                storage_controller_count,
                storage_controller_data,
            ) = helper.get_storage_controller_data()

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
                ]
            },
        )

    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"  # noqa: E501
    )
    def test_get_network_adapter_data_success(self, mock_get_chassis_ids):
        mock_chassis_ids = ["c1", "c2"]
        mock_get_chassis_ids.return_value = mock_chassis_ids

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

        mock_redfish_obj = Mock()
        mock_redfish_obj.get.side_effect = mock_get_response
        self.mock_redfish_client.return_value = mock_redfish_obj

        with RedfishHelper(Mock()) as helper:
            network_adapter_count = helper.get_network_adapter_data()

        self.assertEqual(network_adapter_count, {"c1": 2, "c2": 1})

    @patch("prometheus_hardware_exporter.collectors.redfish.logger")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"  # noqa: E501
    )
    def test_get_network_adapter_data_fail(self, mock_get_chassis_ids, mock_logger):
        mock_redfish_obj = Mock()
        mock_chassis_ids = ["c1"]
        mock_get_chassis_ids.return_value = mock_chassis_ids
        self.mock_redfish_client.return_value = mock_redfish_obj

        response = Mock()
        response.status = 401
        mock_redfish_obj.get.return_value = response

        with RedfishHelper(Mock()) as redfish_helper:
            network_adapter_count = redfish_helper.get_network_adapter_data()

        self.assertEqual(network_adapter_count, {})
        mock_logger.debug.assert_any_call(
            "No network adapters could be found on chassis id: %s", "c1"
        )

    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"  # noqa: E501
    )
    def test_get_chassis_data_success(self, mock_get_chassis_ids):
        mock_chassis_ids = ["c1", "c2"]
        mock_get_chassis_ids.return_value = mock_chassis_ids

        def mock_get_response(uri):
            response = Mock()
            if "/Chassis/c1" in uri:
                response.dict = {
                    "ChassisType": "RackMount",
                    "Manufacturer": "",
                    "Model": "Chassis Model c1",
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            elif "/Chassis/c2" in uri:
                response.dict = {
                    "ChassisType": "RackMount",
                    "Manufacturer": "Dell",
                    "Model": "Chassis Model c2",
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            return response

        mock_redfish_obj = Mock()
        mock_redfish_obj.get.side_effect = mock_get_response
        self.mock_redfish_client.return_value = mock_redfish_obj

        with RedfishHelper(Mock()) as redfish_helper:
            chassis_data = redfish_helper.get_chassis_data()

        self.assertEqual(
            chassis_data,
            {
                "c1": {
                    "chassis_type": "RackMount",
                    "manufacturer": "NA",
                    "model": "Chassis Model c1",
                    "health": "OK",
                    "state": "Enabled",
                },
                "c2": {
                    "chassis_type": "RackMount",
                    "manufacturer": "Dell",
                    "model": "Chassis Model c2",
                    "health": "OK",
                    "state": "Enabled",
                },
            },
        )

    @parameterized.expand(["Storage", "Storages"])
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.collections.get_collection_ids"  # noqa: E501
    )
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_get_storage_drive_data_success(
        self, storage_name, mock_get_system_ids, mock_get_collection_ids
    ):
        mock_system_ids = ["s1"]
        mock_storage_ids = ["STOR1", "STOR2"]

        mock_get_system_ids.return_value = mock_system_ids
        mock_get_collection_ids.return_value = mock_storage_ids

        def mock_get_response(uri):
            response = Mock()
            storage_root = f"Systems/s1/{storage_name}"
            if f"{storage_root}/STOR1/Drives/d11" in uri:
                response.dict = {
                    "Id": "d11",
                    "Status": {"Health": "OK", "State": "Enabled"},
                }

            elif f"{storage_root}/STOR1/Drives/d12" in uri:
                response.dict = {
                    "Id": "d12",
                    "Status": {"Health": "OK", "State": "Disabled"},
                }

            elif f"{storage_root}/STOR2/Drives/d21" in uri:
                response.dict = {
                    "Id": "d21",
                    "Status": {"Health": None, "State": "Enabled"},
                }
            elif f"{storage_root}/STOR1" in uri:
                response.dict = {
                    "Drives": [
                        {"@odata.id": f"/redfish/v1/Systems/s1/{storage_name}/STOR1/Drives/d11"},
                        {"@odata.id": f"/redfish/v1/Systems/s1/{storage_name}/STOR1/Drives/d12"},
                    ]
                }
            elif f"{storage_root}/STOR2" in uri:
                response.dict = {
                    "Drives": [
                        {"@odata.id": f"/redfish/v1/Systems/s1/{storage_name}/STOR2/Drives/d21"},
                    ]
                }
            # response for GET request to /redfish/v1/Systems/<sys_id>/
            elif "Systems" in uri:
                response.dict = {
                    "Storage": {"@odata.id": f"/redfish/v1/Systems/sX/{storage_name}"}
                }
            return response

        mock_redfish_obj = Mock()
        mock_redfish_obj.get.side_effect = mock_get_response
        self.mock_redfish_client.return_value = mock_redfish_obj

        with RedfishHelper(Mock()) as redfish_helper:
            storage_drive_count, storage_drive_data = redfish_helper.get_storage_drive_data()

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

    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_get_memory_dimm_data_success(self, mock_get_system_ids):
        mock_system_ids = ["s1", "s2"]
        mock_get_system_ids.return_value = mock_system_ids

        def mock_get_response(uri):
            response = Mock()
            if "Systems/s1/Memory/dimm1" in uri:
                response.dict = {
                    "Id": "dimm1",
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            elif "Systems/s2/Memory/dimm2" in uri:
                response.dict = {
                    "Id": "dimm2",
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            elif "Systems/s1/Memory" in uri:
                response.dict = {
                    "Members": [
                        {"@odata.id": "/redfish/v1/Systems/s1/Memory/dimm1/"},
                    ]
                }
            elif "Systems/s2/Memory" in uri:
                response.dict = {
                    "Members": [
                        {"@odata.id": "/redfish/v1/Systems/s2/Memory/dimm2/"},
                    ]
                }
            return response

        mock_redfish_obj = Mock()
        mock_redfish_obj.get.side_effect = mock_get_response
        self.mock_redfish_client.return_value = mock_redfish_obj

        with RedfishHelper(Mock()) as redfish_helper:
            memory_dimm_count, memory_dimm_data = redfish_helper.get_memory_dimm_data()

        self.assertEqual(memory_dimm_count, {"s1": 1, "s2": 1})
        self.assertEqual(
            memory_dimm_data,
            {
                "s1": [
                    {
                        "memory_id": "dimm1",
                        "health": "OK",
                        "state": "Enabled",
                    },
                ],
                "s2": [
                    {
                        "memory_id": "dimm2",
                        "health": "OK",
                        "state": "Enabled",
                    },
                ],
            },
        )

    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"  # noqa: E501
    )
    def test_smart_storage_health_data_success(self, mock_get_chassis_ids):
        mock_chassis_ids = ["c1"]
        mock_get_chassis_ids.return_value = mock_chassis_ids

        def mock_get_response(uri):
            response = Mock()
            response.status = 200
            if "Chassis/c1/SmartStorage" in uri:
                response.dict = {
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            return response

        mock_redfish_obj = Mock()
        mock_redfish_obj.get.side_effect = mock_get_response
        self.mock_redfish_client.return_value = mock_redfish_obj

        with RedfishHelper(Mock()) as helper:
            smart_storage_health_data = helper.get_smart_storage_health_data()

        self.assertEqual(
            smart_storage_health_data,
            {
                "c1": {
                    "health": "OK",
                },
            },
        )

    @patch("prometheus_hardware_exporter.collectors.redfish.logger")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"  # noqa: E501
    )
    def test_smart_storage_health_data_fail(self, mock_get_chassis_ids, mock_logger):
        mock_chassis_ids = ["c1"]
        mock_get_chassis_ids.return_value = mock_chassis_ids

        response = Mock()
        response.status = 401
        mock_redfish_obj = Mock()
        mock_redfish_obj.get.return_value = response
        self.mock_redfish_client.return_value = mock_redfish_obj

        with RedfishHelper(Mock()) as redfish_helper:
            smart_storage_health_data = redfish_helper.get_smart_storage_health_data()

        self.assertEqual(
            smart_storage_health_data,
            {},
        )
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Chassis/c1/SmartStorage")
        mock_logger.debug.assert_any_call(
            "Smart Storage URI endpoint not found for chassis ID: %s", "c1"
        )

    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_get_system_id_fail(self, mock_get_system_ids):
        mock_get_system_ids.side_effect = redfish_utilities.systems.RedfishSystemNotFoundError

        mock_redfish_obj = Mock()
        self.mock_redfish_client.return_value = mock_redfish_obj
        with RedfishHelper(Mock()) as redfish_helper:
            processor_count, processor_data = redfish_helper.get_processor_data()
            (
                storage_controller_count,
                storage_controller_data,
            ) = redfish_helper.get_storage_controller_data()
            storage_drive_count, storage_drive_data = redfish_helper.get_storage_drive_data()
            memory_dimm_count, memory_dimm_data = redfish_helper.get_memory_dimm_data()

        self.assertEqual(memory_dimm_count, {})
        self.assertEqual(memory_dimm_data, {})
        self.assertEqual(processor_count, {})
        self.assertEqual(processor_data, {})
        self.assertEqual(storage_controller_count, {})
        self.assertEqual(storage_controller_data, {})
        self.assertEqual(storage_drive_count, {})
        self.assertEqual(storage_drive_data, {})

    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"  # noqa: E501
    )
    def test_get_chassis_id_fail(self, mock_get_chassis_ids):
        mock_get_chassis_ids.side_effect = redfish_utilities.inventory.RedfishChassisNotFoundError

        mock_redfish_obj = Mock()
        self.mock_redfish_client.return_value = mock_redfish_obj
        with RedfishHelper(Mock()) as redfish_helper:
            network_adapter_count = redfish_helper.get_network_adapter_data()
            chassis_data = redfish_helper.get_chassis_data()
            smart_storage_health_data = redfish_helper.get_smart_storage_health_data()

        self.assertEqual(network_adapter_count, {})
        self.assertEqual(chassis_data, {})
        self.assertEqual(smart_storage_health_data, {})


class TestRedfishServiceDiscovery(unittest.TestCase):
    """Test redfish service discovery."""

    @parameterized.expand([SessionCreationError, InvalidCredentialsError])
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_redfish_available_login_fail(self, exc, mock_redfish_client):
        test_ttl = 10
        mock_redfish_obj = Mock()
        mock_redfish_client.return_value = mock_redfish_obj
        mock_redfish_obj.login.side_effect = exc
        discover = RedfishHelper.get_cached_discover_method(ttl=test_ttl)
        host = ""
        available = discover(host)
        self.assertEqual(available, True)

        mock_redfish_client.assert_called()
        mock_redfish_obj.login.assert_called()

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_redfish_available_login_success(self, mock_redfish_client):
        test_ttl = 10
        mock_redfish_obj = Mock()
        mock_redfish_client.return_value = mock_redfish_obj
        discover = RedfishHelper.get_cached_discover_method(ttl=test_ttl)
        host = "mock_host"
        available = discover(host)

        self.assertEqual(available, True)
        mock_redfish_client.assert_called_once_with(
            base_url="mock_host",
            username="",
            password="",
        )
        mock_redfish_obj.login.assert_called_once()
        mock_redfish_obj.logout.assert_called()

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_redfish_not_available(self, mock_redfish_client):
        test_ttl = 10
        mock_redfish_obj = Mock()
        mock_redfish_client.return_value = mock_redfish_obj
        mock_redfish_obj.login.side_effect = RetriesExhaustedError()
        discover = RedfishHelper.get_cached_discover_method(ttl=test_ttl)
        host = "mock_host"
        available = discover(host)

        self.assertEqual(available, False)
        mock_redfish_client.assert_called_once_with(
            base_url="mock_host",
            username="",
            password="",
        )
        mock_redfish_obj.login.assert_called_once()

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_redfish_not_available_generic_error(self, mock_redfish_client):
        test_ttl = 10
        mock_redfish_obj = Mock()
        mock_redfish_client.return_value = mock_redfish_obj
        mock_redfish_obj.login.side_effect = Exception()
        discover = RedfishHelper.get_cached_discover_method(ttl=test_ttl)
        host = "mock_host"
        available = discover(host)

        self.assertEqual(available, False)
        mock_redfish_client.assert_called_once_with(
            base_url="mock_host",
            username="",
            password="",
        )
        mock_redfish_obj.login.assert_called_once()

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_discover_cache(self, mock_redfish_client):
        test_ttl = 1
        mock_redfish_obj = Mock()
        mock_redfish_client.return_value = mock_redfish_obj
        discover = RedfishHelper.get_cached_discover_method(ttl=test_ttl)
        host = "mock_host"
        output = discover(host)
        self.assertEqual(output, True)
        mock_redfish_client.assert_called_once_with(
            base_url="mock_host",
            username="",
            password="",
        )
        mock_redfish_client.reset_mock()

        # output from cache
        output = discover(host)
        self.assertEqual(output, True)
        mock_redfish_client.assert_not_called()

        # wait till cache expires
        sleep(test_ttl + 1)
        output = discover(host)
        self.assertEqual(output, True)
        mock_redfish_client.assert_called_with(
            base_url="mock_host",
            username="",
            password="",
        )

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_redfish_logout_401(self, mock_redfish_client):
        """Test that exception is not raised if logout fails with 401."""
        mock_redfish_obj = Mock()
        mock_redfish_obj.logout.side_effect = BadRequestError(
            "Invalid session resource: /redfish/v1/SessionService/Sessions/132562, "
            "return code: 401"
        )
        mock_redfish_client.return_value = mock_redfish_obj
        with RedfishHelper(Mock()) as redfish_helper:
            self.assertIsNone(redfish_helper.logout())

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_redfish_logout_error(self, mock_redfish_client):
        """Test that exception is raised if logout fails with response not 401."""
        mock_redfish_obj = Mock()
        mock_redfish_obj.logout.side_effect = BadRequestError(
            "Invalid session resource: /redfish/v1/SessionService/Sessions/132562, "
            "return code: 404"
        )
        mock_redfish_client.return_value = mock_redfish_obj
        redfish_helper = RedfishHelper(Mock())
        with self.assertRaises(BadRequestError):
            redfish_helper.logout()
