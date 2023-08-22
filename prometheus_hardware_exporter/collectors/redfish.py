"""Redfish collector."""
from logging import getLogger
from typing import Any, Callable, Dict, List, Optional, Tuple

import redfish
import redfish_utilities
from cachetools.func import ttl_cache
from redfish.rest.v1 import (
    HttpClient,
    RestResponse,
)
from typing_extensions import Self

from prometheus_hardware_exporter.config import Config

logger = getLogger(__name__)

# pylint: disable=too-many-instance-attributes


class RedfishHelper:
    """Helper function for redfish."""

    @staticmethod
    def get_cached_discover_method(ttl: int) -> Callable:
        """Return the cached discover method.

        Passes the ttl value to the cache decorator at runtime.
        """

        @ttl_cache(ttl=ttl)
        def _discover() -> bool:
            """Return true if redfish services have been discovered."""
            logger.info("Discovering redfish services...")
            services = redfish.discover_ssdp()
            if len(services) == 0:
                logger.info("No redfish services discovered")
                return False
            logger.debug("Discovered redfish services: %s", services)
            return True

        return _discover

    def __init__(self, config: Config) -> None:
        """Initialize values for class."""
        self.host = config.redfish_host
        self.username = config.redfish_username
        self.password = config.redfish_password
        self.timeout = config.redfish_client_timeout
        self.max_retry = config.redfish_client_max_retry
        self.redfish_obj: HttpClient = None

    def __enter__(self) -> Self:
        """Login to redfish while entering context manager."""
        self.redfish_obj = redfish.redfish_client(
            base_url=self.host,
            username=self.username,
            password=self.password,
            timeout=self.timeout,
            max_retry=self.max_retry,
        )
        self.redfish_obj.login(auth="session")
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
    ) -> None:
        """Logout from redfish while exiting context manager."""
        if self.redfish_obj is not None:
            self.redfish_obj.logout()

    def get_sensor_data(self) -> Dict[str, List]:
        """Get sensor data.

        Returns:
            sensor_data: a dictionary where key, value maps to chassis name, sensor data.
        """
        data = self._retrieve_redfish_sensor_data()
        return self._map_sensor_data_to_chassis(data)

    def _map_sensor_data_to_chassis(self, sensor_data: List[Any]) -> Dict[str, List]:
        """Return dictionary with sensor data mapped to chassis."""
        output = {}
        for chassis in sensor_data:
            output[str(chassis["ChassisName"])] = [
                {
                    "Sensor": sensor["Name"],
                    "Reading": str(sensor["Reading"]) + (sensor["Units"] or ""),
                    "Health": sensor["Health"] or "N/A",
                }
                for sensor in chassis["Readings"]
            ]
        return output

    def _retrieve_redfish_sensor_data(self) -> List[Any]:
        """Return sensor if sensor exists else None.

        Returns:
            sensors: List of dicts with details for each sensor
        """
        sensors: List[Any] = []

        logger.info("Getting redfish sensor info...")
        sensors = redfish_utilities.get_sensors(self.redfish_obj)
        return sensors

    def _verify_redfish_call(self, redfish_obj: HttpClient, uri: str) -> Optional[Dict[str, Any]]:
        """Return REST response for GET request API call on the URI.

        Returns None if URI isn't present.
        """
        resp: RestResponse = redfish_obj.get(uri)
        if resp.status == 200:
            return resp.dict
        logger.debug("Not able to query from URI: %s.", uri)
        return None

    def get_processor_data(self) -> Tuple[Dict[str, int], Dict[str, List]]:
        """Return processor data and count.

        Returns:
            processor_count: Dict of system ids mapped to the total number
            of processors on that system.
            processor_data: Dict of system ids mapped to list of processors on that system.

        Example of processor_count: {"sys1": 2, "sys2": 1}

        Example of processor_data:
        {
            "sys1": [
                {
                    "processor_id": "p11",
                    "model": "Processor sys1 Model 1",
                    "health": "OK",
                    "state": "Enabled",
                },
                {
                    "processor_id": "p12",
                    "model": "Processor sys1 Model 2",
                    "health": "Warning",
                    "state": "Disabled",
                },
            ],
            "sys2": [
                {
                    "processor_id": "p21",
                    "model": "Processor sys2 Model 1",
                    "health": "OK",
                    "state": "Enabled",
                },
            ],
        }
        """
        processor_data: Dict[str, List] = {}
        processor_count: Dict[str, int] = {}
        processors_root_uri_pattern = "/redfish/v1/Systems/{}/Processors"
        logger.info("Getting processor data...")

        try:
            system_ids: List[str] = redfish_utilities.systems.get_system_ids(self.redfish_obj)
        except redfish_utilities.systems.RedfishSystemNotFoundError:
            logger.debug("No system instances found.")
            return processor_count, processor_data

        for system_id in system_ids:
            processor_uris: List[str] = []
            # eg: /redfish/v1/Systems/1/Processors
            processors_root_uri = processors_root_uri_pattern.format(system_id)
            processor_members: List[Dict] = self.redfish_obj.get(processors_root_uri).dict[
                "Members"
            ]
            for member in processor_members:
                processor_uris.append(member["@odata.id"])
            processor_count[system_id] = len(processor_uris)
            processor_data_in_curr_system: List[Dict] = []
            for processor_uri in processor_uris:
                # eg: /redfish/v1/Systems/1/Processors/{1,2}
                processor = self.redfish_obj.get(processor_uri).dict
                processor_data_in_curr_system.append(
                    {
                        "processor_id": processor["Id"],
                        "model": processor["Model"] or "NA",
                        "health": processor["Status"]["Health"] or "NA",
                        "state": processor["Status"]["State"],
                    }
                )
            processor_data[system_id] = processor_data_in_curr_system
        logger.debug("Processor count: %s", processor_count)
        logger.debug("Processor data: %s", processor_data)
        return processor_count, processor_data

    def get_storage_controller_data(self) -> Tuple[Dict[str, int], Dict[str, List]]:
        """Return storage controller data and count.

        Returns:
            storage_controller_count: Dict of system ids mapped to the total number
            of storage controllers on that system.
            storage_controller_data: Dict of system ids mapped to list of storage
            controllers on that system.

        Example of storage_controller_count: {"sys1": 2}

        Example of storage_controller_data:
        {
            "sys1": [
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
        }

        """
        storage_controller_data: Dict[str, List] = {}
        # storage controllers on each system
        storage_controller_count: Dict[str, int] = {}
        storage_root_uri_pattern = "/redfish/v1/Systems/{}/Storage"
        logger.info("Getting storage controller data...")

        try:
            system_ids: List[str] = redfish_utilities.systems.get_system_ids(self.redfish_obj)
        except redfish_utilities.systems.RedfishSystemNotFoundError:
            logger.debug("No system instances found.")
            return storage_controller_count, storage_controller_data

        for system_id in system_ids:
            storage_controller_count[system_id] = 0

            # List of storage ids
            storage_ids: List[str] = redfish_utilities.collections.get_collection_ids(
                self.redfish_obj, storage_root_uri_pattern.format(system_id)
            )
            storage_controller_data_in_curr_system = []
            for storage_id in storage_ids:
                # eg: /redfish/v1/Systems/1/Storage/XYZ123
                curr_storage_uri = storage_root_uri_pattern.format(system_id) + "/" + storage_id

                # list of storage controllers for that storage id
                storage_controllers_list: List[Dict] = self.redfish_obj.get(curr_storage_uri).dict[
                    "StorageControllers"
                ]
                storage_controller_count[system_id] += len(storage_controllers_list)

                # picking out the required data from each storage controller in the list
                for data in storage_controllers_list:
                    storage_controller_data_in_curr_system.append(
                        {
                            "storage_id": storage_id,
                            "controller_id": data["MemberId"],
                            "state": data["Status"]["State"],
                            "health": data["Status"]["Health"] or "NA",
                        }
                    )

            storage_controller_data[system_id] = storage_controller_data_in_curr_system

        logger.debug("storage controller count: %s", storage_controller_count)
        logger.debug("storage controller data: %s", storage_controller_data)
        return storage_controller_count, storage_controller_data

    def get_network_adapter_data(self) -> Dict[str, int]:
        """Return dict of chassis ids mapped to number of network adapters on that chassis.

        Example of network_adapter_count: {"chass1": 1, "chass2": 2}
        """
        network_adapter_count: Dict[str, int] = {}
        network_adapters_root_uri_pattern = "/redfish/v1/Chassis/{}/NetworkAdapters"
        logger.info("Getting network adapter data...")

        try:
            chassis_ids: List[str] = redfish_utilities.inventory.get_chassis_ids(self.redfish_obj)
        except redfish_utilities.inventory.RedfishChassisNotFoundError:
            logger.debug("No chassis instances found.")
            return network_adapter_count

        for chassis_id in chassis_ids:
            # eg: /redfish/v1/Chassis/1/NetworkAdapters
            network_adapters_root_uri = network_adapters_root_uri_pattern.format(chassis_id)
            network_adapters: Optional[Dict[str, Any]] = self._verify_redfish_call(
                self.redfish_obj, network_adapters_root_uri
            )
            if not network_adapters:
                logger.debug("No network adapters could be found on chassis id: %s", chassis_id)
                print("here")
                continue
            logger.debug("Network adapters: %s", network_adapters)
            network_adapter_count[chassis_id] = len(network_adapters["Members"])

        logger.debug("Network adapter count: %s", network_adapter_count)
        return network_adapter_count

    def get_chassis_data(self) -> Dict[str, Dict]:
        """Return chassis data.

        The returned chassis_data is a dict of chassis ids each mapped to a
        dict of data for that chassis.

        Example of chassis_data:
        {
            "chass1": {
                "chassis_type": "RackMount",
                "manufacturer": "",
                "model": "Chassis Model chass1",
                "health": "OK",
                "state": "Enabled",
            },
            "chass2": {
                "chassis_type": "RackMount",
                "manufacturer": "",
                "model": "Chassis Model chass2",
                "health": "OK",
                "state": "Enabled",
            },
        }
        """
        chassis_data: Dict[str, Dict] = {}
        chassis_root_uri_pattern = "/redfish/v1/Chassis/{}"
        logger.info("Getting chassis data...")

        try:
            chassis_ids: List[str] = redfish_utilities.inventory.get_chassis_ids(self.redfish_obj)
        except redfish_utilities.inventory.RedfishChassisNotFoundError:
            logger.debug("No chassis instances found.")
            return chassis_data

        for chassis_id in chassis_ids:
            # /redfish/v1/Chassis/1
            chassis_uri = chassis_root_uri_pattern.format(chassis_id)
            curr_chassis: Dict[str, Any] = self.redfish_obj.get(chassis_uri).dict
            chassis_data[chassis_id] = {
                "chassis_type": curr_chassis["ChassisType"] or "NA",
                "manufacturer": curr_chassis["Manufacturer"] or "NA",
                "model": curr_chassis["Model"] or "NA",
                "health": curr_chassis["Status"]["Health"] or "NA",
                "state": curr_chassis["Status"]["State"],
            }

        logger.debug("Chassis data: %s", chassis_data)
        return chassis_data

    def get_storage_drive_data(self) -> Tuple[Dict[str, int], Dict[str, List]]:
        """Return storage drive data and count.

        Returns:
            storage_drive_count: Dict of system ids mapped to the total number
            of storage drives on that system.
            storage_drive_data: Dict of system ids mapped to list of storage
            drives on that system.

        Example of storage_drive_count: {"sys1": 1, "sys2": 1}

        Example of storage_drive_data:
        {
            "sys1": [
                {
                    "storage_id": "STOR1",
                    "drive_id": "d11",
                    "health": "OK",
                    "state": "Enabled",
                },
            ],
            "sys2": [
                {
                    "storage_id": "STOR2",
                    "drive_id": "d21",
                    "health": "OK",
                    "state": "Enabled",
                },
            ],
        },
        """
        storage_drive_data: Dict[str, List] = {}
        # storage drives on each system
        storage_drive_count: Dict[str, int] = {}
        storage_root_uri_pattern = "/redfish/v1/Systems/{}/Storage"
        logger.info("Getting storage drive data...")

        try:
            system_ids: List[str] = redfish_utilities.systems.get_system_ids(self.redfish_obj)
        except redfish_utilities.systems.RedfishSystemNotFoundError:
            logger.debug("No system instances found.")
            return storage_drive_count, storage_drive_data

        for system_id in system_ids:
            storage_drive_count[system_id] = 0

            storage_ids: List[str] = redfish_utilities.collections.get_collection_ids(
                self.redfish_obj, storage_root_uri_pattern.format(system_id)
            )
            storage_drive_data_in_curr_system: List[Dict] = []
            for storage_id in storage_ids:
                # /redfish/v1/Systems/1/Storage/XYZ123/
                curr_storage_uri = storage_root_uri_pattern.format(system_id) + "/" + storage_id
                # list of storage drives for that storage id
                storage_drives_list: List[Dict] = self.redfish_obj.get(curr_storage_uri).dict[
                    "Drives"
                ]
                storage_drive_count[system_id] += len(storage_drives_list)

                storage_drive_uris: List[str] = [
                    storage_drive["@odata.id"] for storage_drive in storage_drives_list
                ]

                for uri in storage_drive_uris:
                    data = self.redfish_obj.get(uri).dict
                    storage_drive_data_in_curr_system.append(
                        {
                            "storage_id": storage_id,
                            "drive_id": data["Id"],
                            "state": data["Status"]["State"],
                            "health": data["Status"]["Health"] or "NA",
                        }
                    )

            storage_drive_data[system_id] = storage_drive_data_in_curr_system

        logger.debug("storage drive count: %s", storage_drive_count)
        logger.debug("storage drive data: %s", storage_drive_data)
        return storage_drive_count, storage_drive_data

    def get_memory_dimm_data(self) -> Tuple[Dict[str, int], Dict[str, List]]:
        """Return memory dimm data and count.

        Returns:
            memory_dimm_count: Dict of system ids mapped to the total number
            of memory dimms on that system.
            memory_dimm_data: Dict of system ids mapped to list of memory dimms
            on that system.

        Example of memory_dimm_count: {"s1": 1, "s2": 1}

        Example of memory_dimm_data:
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
        """
        memory_dimm_data: Dict[str, List] = {}
        memory_dimm_count: Dict[str, int] = {}
        memory_root_uri_pattern = "/redfish/v1/Systems/{}/Memory"
        logger.info("Getting memory dimm data...")

        try:
            system_ids: List[str] = redfish_utilities.systems.get_system_ids(self.redfish_obj)
        except redfish_utilities.systems.RedfishSystemNotFoundError:
            logger.debug("No system instances found.")
            return memory_dimm_count, memory_dimm_data

        for system_id in system_ids:
            # /redfish/v1/Systems/1/Memory
            memory_dimm_uris: List[str] = []
            memory_root_uri = memory_root_uri_pattern.format(system_id)
            curr_memory_data: Dict[str, Any] = self.redfish_obj.get(memory_root_uri).dict
            for member in curr_memory_data["Members"]:
                memory_dimm_uris.append(member["@odata.id"])
            memory_dimm_count[system_id] = len(memory_dimm_uris)
            memory_dimm_data_in_curr_system: List[Dict] = []
            for memory_dimm_uri in memory_dimm_uris:
                # /redfish/v1/Systems/1/Memory/{proc1dimm1, proc1dimm2...}
                memory_dimm: Dict[str, Any] = self.redfish_obj.get(memory_dimm_uri).dict
                memory_dimm_data_in_curr_system.append(
                    {
                        "memory_id": memory_dimm["Id"],
                        "health": memory_dimm["Status"]["Health"] or "NA",
                        "state": memory_dimm["Status"]["State"],
                    }
                )
            memory_dimm_data[system_id] = memory_dimm_data_in_curr_system

        logger.debug("memory dimm count: %s", memory_dimm_count)
        logger.debug("memory dimm data: %s", memory_dimm_data)
        return memory_dimm_count, memory_dimm_data

    def get_smart_storage_health_data(self) -> Dict[str, Any]:
        """Return Smart Storage health data if present on the chassis.

        Returns a dict of chassis ids mapped to the smart storage health data on that chassis.
        """
        smart_storage_health_data: Dict[str, Any] = {}
        smart_storage_root_uri_pattern = "/redfish/v1/Chassis/{}/SmartStorage"
        logger.info("Getting smart storage health data...")

        try:
            chassis_ids: List[str] = redfish_utilities.inventory.get_chassis_ids(self.redfish_obj)
        except redfish_utilities.inventory.RedfishChassisNotFoundError:
            logger.debug("No chassis instances found.")
            return smart_storage_health_data

        for chassis_id in chassis_ids:
            smart_storage_uri = smart_storage_root_uri_pattern.format(chassis_id)
            smart_storage_data: Optional[Dict[str, Any]] = self._verify_redfish_call(
                self.redfish_obj, smart_storage_uri
            )
            if not smart_storage_data:
                logger.debug("Smart Storage URI endpoint not found for chassis ID: %s", chassis_id)
                continue
            smart_storage_health_data[chassis_id] = {
                "health": smart_storage_data["Status"]["Health"] or "NA",
            }

        logger.debug("smart storage health data: %s", smart_storage_health_data)
        return smart_storage_health_data
