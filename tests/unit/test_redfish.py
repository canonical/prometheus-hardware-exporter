import unittest
from time import sleep
from unittest.mock import Mock, patch

import redfish_utilities
from redfish.rest.v1 import (
    InvalidCredentialsError,
    RetriesExhaustedError,
    SessionCreationError,
)

from prometheus_hardware_exporter.collectors.redfish import RedfishHelper
from prometheus_hardware_exporter.config import Config


class TestRedfishMetrics(unittest.TestCase):
    """Test metrics methods in RedfishHelper."""

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_redfish_helper_context_manager_success(self, mock_redfish_client):
        mock_redfish_login = Mock()
        mock_redfish_logout = Mock()
        mock_redfish_client.return_value.login = mock_redfish_login
        mock_redfish_client.return_value.logout = mock_redfish_logout
        mock_config = Config(
            redfish_host="",
            redfish_username="",
            redfish_password="",
            redfish_client_timeout=10,
            redfish_client_max_retry=5,
            redfish_discover_cache_ttl=5,
        )
        with RedfishHelper(mock_config):
            mock_redfish_client.assert_called_once_with(
                base_url="",
                username="",
                password="",
                timeout=10,
                max_retry=5,
            )
            mock_redfish_login.assert_called_once_with(auth="session")
        mock_redfish_logout.assert_called_once()

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_redfish_helper_context_manager_fail(self, mock_redfish_client):
        mock_config = Config(
            redfish_host="",
            redfish_username="",
            redfish_password="",
            redfish_client_timeout=10,
            redfish_client_max_retry=5,
            redfish_discover_cache_ttl=5,
        )
        for err in [
            InvalidCredentialsError(),
            ConnectionError(),
            SessionCreationError(),
            RetriesExhaustedError(),
        ]:
            mock_redfish_client.side_effect = err
            with self.assertRaises(
                (
                    InvalidCredentialsError,
                    ConnectionError,
                    SessionCreationError,
                    RetriesExhaustedError,
                )
            ):
                with RedfishHelper(mock_config):
                    pass

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_verify_redfish_call_success(self, mock_redfish_client):
        uri = "/some/test/uri"
        mock_redfish_obj = Mock()
        mock_response = Mock()

        mock_redfish_obj.get.return_value = mock_response
        mock_response.status = 200
        mock_response.dict = {"foo": 1, "bar": 2}

        with RedfishHelper(Mock()) as helper:
            resp_dict = helper._verify_redfish_call(mock_redfish_obj, uri)

        self.assertEqual(resp_dict, {"foo": 1, "bar": 2})
        mock_redfish_obj.get.assert_called_with(uri)

    @patch("prometheus_hardware_exporter.collectors.redfish.logger")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_verify_redfish_call_fail(self, mock_redfish_client, mock_logger):
        uri = "/some/test/uri"
        mock_redfish_obj = Mock()
        mock_response = Mock()

        mock_redfish_obj.get.return_value = mock_response
        mock_response.status = 401

        with RedfishHelper(Mock()) as helper:
            resp_dict = helper._verify_redfish_call(mock_redfish_obj, uri)

        mock_redfish_obj.get.assert_called_with(uri)
        mock_logger.debug.assert_called_with("Not able to query from URI: %s.", "/some/test/uri")
        self.assertIsNone(resp_dict)

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
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
    def test_get_sensor_data_success(self, mock_sensor_data, mock_redfish_client):
        with RedfishHelper(Mock()) as helper:
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

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
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
    def test_get_multiple_chassis_sensor_data_success(self, mock_sensor_data, mock_redfish_client):
        with RedfishHelper(Mock()) as helper:
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

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch.object(RedfishHelper, "_retrieve_redfish_sensor_data", return_value=[])
    def test_get_sensor_data_fail(self, mock_sensor_data, mock_redfish_client):
        with RedfishHelper(Mock()) as helper:
            data = helper.get_sensor_data()
        self.assertEqual(data, {})

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_map_sensor_data_to_chassis(self, mock_redfish_client):
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

        with RedfishHelper(Mock()) as helper:
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
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_retrieve_redfish_sensor_data_success(self, mock_redfish_client, mock_get_sensors):
        mock_get_sensors.return_value = ["return_data"]

        mock_redfish_obj = Mock()
        mock_redfish_client.return_value = mock_redfish_obj
        with RedfishHelper(Mock()) as helper:
            data = helper._retrieve_redfish_sensor_data()
        self.assertEqual(data, ["return_data"])

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_get_processor_data_success(self, mock_get_system_ids, mock_redfish_client):
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

        with RedfishHelper(Mock()) as helper:
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

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test__storage_root_uri(self, mock_redfish_client):
        """Test RedfishHelper._storage_root_uri method."""
        mock_redfish_client.return_value = Mock()

        for storage_name in ["Storage", "Storages", "TestStorage"]:
            expected_uri = f"/redfish/v1/Systems/S1/{storage_name}/"
            with RedfishHelper(Mock()) as helper:
                uri = helper._storage_root_uri("S1", storage_name)
            assert uri == expected_uri

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.collections.get_collection_ids"  # noqa: E501
    )
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_get_storage_controller_data_success(
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
    def test_non_standard_storage_uri_name(
        self, mock_get_system_ids, mock_get_collection_ids, mock_redfish_client
    ):
        """Test non-standard name for "Storage" in URI for storage controller and drives.

        Eg: /redfish/v1/Systems/S1/Storages
        """
        mock_redfish_obj = Mock()
        mock_get_system_ids.return_value = ["s1"]
        mock_get_collection_ids.return_value = ["STOR1"]
        mock_redfish_client.return_value = mock_redfish_obj

        def mock_get_response(uri):
            response = Mock()
            if "Systems/s1/Storages/STOR1/Drives/d11" in uri:
                response.dict = {
                    "Id": "d11",
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            elif "Systems/s1/Storages/STOR1" in uri:
                response.dict = {
                    "StorageControllers": [
                        {
                            "MemberId": "sc0",
                            "Status": {"Health": "OK", "State": "Enabled"},
                        }
                    ],
                    "Drives": [
                        {"@odata.id": "/redfish/v1/Systems/s1/Storages/STOR1/Drives/d11"},
                    ],
                }
            # response for GET request to /redfish/v1/Systems/<sys_id>/
            elif "Systems" in uri:
                response.dict = {"Storage": {"@odata.id": "/redfish/v1/Systems/sX/Storages"}}
            return response

        mock_redfish_obj.get.side_effect = mock_get_response

        with RedfishHelper(Mock()) as helper:
            sc_count, sc_data = helper.get_storage_controller_data()
            drive_count, drive_data = helper.get_storage_drive_data()

        # storage controller
        self.assertEqual(sc_count, {"s1": 1})
        self.assertEqual(
            sc_data,
            {
                "s1": [
                    {
                        "storage_id": "STOR1",
                        "controller_id": "sc0",
                        "health": "OK",
                        "state": "Enabled",
                    },
                ],
            },
        )

        # storage drives
        self.assertEqual(drive_count, {"s1": 1})
        self.assertEqual(
            drive_data,
            {
                "s1": [
                    {
                        "storage_id": "STOR1",
                        "drive_id": "d11",
                        "health": "OK",
                        "state": "Enabled",
                    },
                ],
            },
        )

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"  # noqa: E501
    )
    def test_get_network_adapter_data_success(self, mock_get_chassis_ids, mock_redfish_client):
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

        with RedfishHelper(Mock()) as helper:
            network_adapter_count = helper.get_network_adapter_data()

        self.assertEqual(network_adapter_count, {"c1": 2, "c2": 1})

    @patch("prometheus_hardware_exporter.collectors.redfish.logger")
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"  # noqa: E501
    )
    def test_get_network_adapter_data_fail(
        self, mock_get_chassis_ids, mock_redfish_client, mock_logger
    ):
        mock_redfish_obj = Mock()
        mock_chassis_ids = ["c1"]
        mock_get_chassis_ids.return_value = mock_chassis_ids
        mock_redfish_client.return_value = mock_redfish_obj

        response = Mock()
        response.status = 401
        mock_redfish_obj.get.return_value = response

        with RedfishHelper(Mock()) as helper:
            network_adapter_count = helper.get_network_adapter_data()

        self.assertEqual(network_adapter_count, {})
        mock_logger.debug.assert_any_call(
            "No network adapters could be found on chassis id: %s", "c1"
        )

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"  # noqa: E501
    )
    def test_get_chassis_data_success(self, mock_get_chassis_ids, mock_redfish_client):
        mock_chassis_ids = ["c1", "c2"]
        mock_redfish_obj = Mock()
        mock_get_chassis_ids.return_value = mock_chassis_ids
        mock_redfish_client.return_value = mock_redfish_obj

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

        mock_redfish_obj.get.side_effect = mock_get_response

        with RedfishHelper(Mock()) as helper:
            chassis_data = helper.get_chassis_data()

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

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.collections.get_collection_ids"  # noqa: E501
    )
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_get_storage_drive_data_success(
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
            # response for GET request to /redfish/v1/Systems/<sys_id>/
            elif "Systems" in uri:
                response.dict = {"Storage": {"@odata.id": "/redfish/v1/Systems/sX/Storage"}}
            return response

        mock_redfish_obj.get.side_effect = mock_get_response

        with RedfishHelper(Mock()) as helper:
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

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_get_memory_dimm_data_success(self, mock_get_system_ids, mock_redfish_client):
        mock_redfish_obj = Mock()
        mock_system_ids = ["s1", "s2"]
        mock_get_system_ids.return_value = mock_system_ids
        mock_redfish_client.return_value = mock_redfish_obj

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

        mock_redfish_obj.get.side_effect = mock_get_response

        with RedfishHelper(Mock()) as helper:
            memory_dimm_count, memory_dimm_data = helper.get_memory_dimm_data()

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

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"  # noqa: E501
    )
    def test_smart_storage_health_data_success(self, mock_get_chassis_ids, mock_redfish_client):
        mock_chassis_ids = ["c1"]
        mock_redfish_obj = Mock()
        mock_get_chassis_ids.return_value = mock_chassis_ids
        mock_redfish_client.return_value = mock_redfish_obj

        def mock_get_response(uri):
            response = Mock()
            response.status = 200
            if "Chassis/c1/SmartStorage" in uri:
                response.dict = {
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            return response

        mock_redfish_obj.get.side_effect = mock_get_response

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
    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"  # noqa: E501
    )
    def test_smart_storage_health_data_fail(
        self, mock_get_chassis_ids, mock_redfish_client, mock_logger
    ):
        mock_chassis_ids = ["c1"]
        mock_redfish_obj = Mock()
        mock_get_chassis_ids.return_value = mock_chassis_ids
        mock_redfish_client.return_value = mock_redfish_obj

        response = Mock()
        response.status = 401
        mock_redfish_obj.get.return_value = response

        with RedfishHelper(Mock()) as helper:
            smart_storage_health_data = helper.get_smart_storage_health_data()

        self.assertEqual(
            smart_storage_health_data,
            {},
        )
        mock_redfish_obj.get.assert_any_call("/redfish/v1/Chassis/c1/SmartStorage")
        mock_logger.debug.assert_any_call(
            "Smart Storage URI endpoint not found for chassis ID: %s", "c1"
        )

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.systems.get_system_ids"
    )
    def test_get_system_id_fail(self, mock_get_system_ids, mock_redfish_client):
        mock_redfish_obj = Mock()
        mock_get_system_ids.side_effect = redfish_utilities.systems.RedfishSystemNotFoundError

        mock_redfish_client.return_value = mock_redfish_obj
        with RedfishHelper(Mock()) as helper:
            processor_count, processor_data = helper.get_processor_data()
            (
                storage_controller_count,
                storage_controller_data,
            ) = helper.get_storage_controller_data()
            storage_drive_count, storage_drive_data = helper.get_storage_drive_data()
            memory_dimm_count, memory_dimm_data = helper.get_memory_dimm_data()

        self.assertEqual(memory_dimm_count, {})
        self.assertEqual(memory_dimm_data, {})
        self.assertEqual(processor_count, {})
        self.assertEqual(processor_data, {})
        self.assertEqual(storage_controller_count, {})
        self.assertEqual(storage_controller_data, {})
        self.assertEqual(storage_drive_count, {})
        self.assertEqual(storage_drive_data, {})

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    @patch(
        "prometheus_hardware_exporter.collectors.redfish.redfish_utilities.inventory.get_chassis_ids"  # noqa: E501
    )
    def test_get_chassis_id_fail(self, mock_get_chassis_ids, mock_redfish_client):
        mock_redfish_obj = Mock()
        mock_get_chassis_ids.side_effect = redfish_utilities.inventory.RedfishChassisNotFoundError

        mock_redfish_client.return_value = mock_redfish_obj
        with RedfishHelper(Mock()) as helper:
            network_adapter_count = helper.get_network_adapter_data()
            chassis_data = helper.get_chassis_data()
            smart_storage_health_data = helper.get_smart_storage_health_data()

        self.assertEqual(network_adapter_count, {})
        self.assertEqual(chassis_data, {})
        self.assertEqual(smart_storage_health_data, {})


class TestRedfishServiceDiscovery(unittest.TestCase):
    """Test redfish service discovery."""

    @patch("prometheus_hardware_exporter.collectors.redfish.redfish_client")
    def test_redfish_available_login_fail(self, mock_redfish_client):
        test_ttl = 10
        mock_redfish_obj = Mock()
        mock_redfish_client.return_value = mock_redfish_obj
        for exc in [SessionCreationError, InvalidCredentialsError]:
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
