"""Redfish collector."""
from logging import getLogger
from typing import Any, Callable, Dict, List, Optional, Tuple

import redfish
import redfish_utilities
from cachetools.func import ttl_cache
from redfish.rest.v1 import (
    HttpClient,
    InvalidCredentialsError,
    RestResponse,
    RetriesExhaustedError,
    SessionCreationError,
)

from prometheus_hardware_exporter.config import Config

logger = getLogger(__name__)

# pylint: disable=too-many-instance-attributes


class RedfishHelper:
    """Helper function for redfish."""

    def __init__(self, config: Config) -> None:
        """Initialize values for class"""
        self.host = config.redfish_host
        self.username = config.redfish_username
        self.password = config.redfish_password
        self.timeout = config.redfish_client_timeout
        self.max_retry = config.redfish_client_max_retry
        self.discover = self.get_discover(config.redfish_discover_cache_ttl)

        self.sys_inventory: Optional[List[Dict[str, Any]]] = None
        self.redfish_obj: Optional[HttpClient] = None

    def _get_redfish_obj(self) -> Optional[HttpClient]:
        """Return a new redfish object."""
        try:
            self.redfish_obj = redfish.redfish_client(
                base_url=self.host,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                max_retry=self.max_retry,
            )
            self.redfish_obj.login(auth="session")
            logger.info("Logging into redfish service...")
        except (
            InvalidCredentialsError,
            SessionCreationError,
            ConnectionError,
            RetriesExhaustedError,
        ) as err:
            logger.exception(err)

        return self.redfish_obj

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

        redfish_obj: Optional[HttpClient] = self._get_redfish_obj()
        if redfish_obj:
            logger.info("Getting redfish sensor info...")
            sensors = redfish_utilities.get_sensors(redfish_obj)
            redfish_obj.logout()
        return sensors

    def _verify_redfish_call(self, redfish_obj: HttpClient, uri: str) -> Optional[Dict[str, Any]]:
        """Return REST response for GET request API call on the URI.

        Returns None if URI isn't present.
        """
        resp: RestResponse = redfish_obj.get(uri)
        if resp.status == 200:
            return resp.dict
        logger.info("Not able to query from URI: %s.", uri)
        return None

    def get_processor_data(self) -> Tuple[Dict[str, int], Dict[str, List]]:
        """Return processor data and count.

        Returns:
            processor_count: Dict of system ids mapped to the total number
            of processors on that system.
            processor_data: Dict of system ids mapped to list of processors on that system.
        """
        processor_data: Dict[str, List] = {}
        processor_count: Dict[str, int] = {}
        processors_root_uri_pattern = "/redfish/v1/Systems/{}/Processors"
        redfish_obj: Optional[HttpClient] = self._get_redfish_obj()

        if redfish_obj:
            try:
                system_ids: List[str] = redfish_utilities.systems.get_system_ids(redfish_obj)
            except redfish_utilities.systems.RedfishSystemNotFoundError:
                logger.info("No system instances found.")
                return processor_count, processor_data

            for system_id in system_ids:
                processor_uris: List[str] = []
                # eg: /redfish/v1/Systems/1/Processors
                processors_root_uri = processors_root_uri_pattern.format(system_id)
                processor_members: Dict[str, Any] = redfish_obj.get(processors_root_uri).dict[
                    "Members"
                ]
                for member in processor_members:
                    processor_uris.append(member["@odata.id"])
                processor_count[system_id] = len(processor_uris)
                processor_data_in_curr_system: List[Dict] = []
                for processor_uri in processor_uris:
                    # eg: /redfish/v1/Systems/1/Processors/{1,2}
                    processor = redfish_obj.get(processor_uri).dict
                    processor_data_in_curr_system.append(
                        {
                            "processor_id": processor["Id"],
                            "model": processor["Model"],
                            "health": processor["Status"]["Health"] or "NA",
                            "state": processor["Status"]["State"],
                        }
                    )
                processor_data[system_id] = processor_data_in_curr_system
            redfish_obj.logout()
        logger.info("Processor count: %s", processor_count)
        logger.info("Processor data: %s", processor_data)
        return processor_count, processor_data

    def get_storage_controller_data(self) -> Tuple[Dict[str, int], Dict[str, List]]:
        """Return storage controller data and count.

        Returns:
            storage_controller_count: Dict of system ids mapped to the total number
            of storage controllers on that system.
            storage_controller_data: Dict of system ids mapped to list of storage
            controllers on that system.
        """
        storage_controller_data: Dict[str, List] = {}
        # storage controllers on each system
        storage_controller_count: Dict[str, int] = {}
        storage_root_uri_pattern = "/redfish/v1/Systems/{}/Storage"
        redfish_obj: Optional[HttpClient] = self._get_redfish_obj()

        if redfish_obj:
            try:
                system_ids: List[str] = redfish_utilities.systems.get_system_ids(redfish_obj)
            except redfish_utilities.systems.RedfishSystemNotFoundError:
                logger.info("No system instances found.")
                return storage_controller_count, storage_controller_data

            for system_id in system_ids:
                storage_controller_count[system_id] = 0

                # List of storage ids
                storage_ids: List[str] = redfish_utilities.collections.get_collection_ids(
                    redfish_obj, storage_root_uri_pattern.format(system_id)
                )
                storage_controller_data_in_curr_system = []
                for storage_id in storage_ids:
                    # eg: /redfish/v1/Systems/1/Storage/XYZ123
                    curr_storage_uri = (
                        storage_root_uri_pattern.format(system_id) + "/" + storage_id
                    )

                    # list of storage controllers for that storage id
                    storage_controllers_list: List[Dict] = redfish_obj.get(curr_storage_uri).dict[
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

            redfish_obj.logout()

        logger.info("storage controller count: %s", storage_controller_count)
        logger.info("storage controller data: %s", storage_controller_data)
        return storage_controller_count, storage_controller_data

    def get_network_adapter_data(self) -> Dict[str, int]:
        """Return dict of chassis ids mapped to number of network adapters on that chassis."""
        network_adapter_count: Dict[str, int] = {}
        network_adapters_root_uri_pattern = "/redfish/v1/Chassis/{}/NetworkAdapters"
        redfish_obj: Optional[HttpClient] = self._get_redfish_obj()
        if redfish_obj:
            try:
                chassis_ids: List[str] = redfish_utilities.inventory.get_chassis_ids(redfish_obj)
            except redfish_utilities.inventory.RedfishChassisNotFoundError:
                logger.info("No chassis instances found.")
                return network_adapter_count

            for chassis_id in chassis_ids:
                # eg: /redfish/v1/Chassis/1/NetworkAdapters
                network_adapters_root_uri = network_adapters_root_uri_pattern.format(chassis_id)
                network_adapters: Optional[Dict[str, Any]] = self._verify_redfish_call(
                    redfish_obj, network_adapters_root_uri
                )
                if not network_adapters:
                    logger.info("No network adapters could be found on chassis id: %s", chassis_id)
                    redfish_obj.logout()
                    continue
                logger.info("Network adapters: %s", network_adapters)
                network_adapter_count[chassis_id] = len(network_adapters["Members"])
            redfish_obj.logout()
        logger.info("Network adapter count: %s", network_adapter_count)
        return network_adapter_count

    def get_chassis_data(self) -> Dict[str, Dict]:
        """Return chassis data.

        The returned chassis_data is a dict of chassis ids each mapped to a
        dict of data for that chassis.
        """
        chassis_data: Dict[str, Dict] = {}
        chassis_root_uri_pattern = "/redfish/v1/Chassis/{}"
        redfish_obj: Optional[HttpClient] = self._get_redfish_obj()
        if redfish_obj:
            try:
                chassis_ids: List[str] = redfish_utilities.inventory.get_chassis_ids(redfish_obj)
            except redfish_utilities.inventory.RedfishChassisNotFoundError:
                logger.info("No chassis instances found.")
                return chassis_data

            for chassis_id in chassis_ids:
                # /redfish/v1/Chassis/1
                chassis_uri = chassis_root_uri_pattern.format(chassis_id)
                curr_chassis: Dict[str, Any] = redfish_obj.get(chassis_uri).dict
                chassis_data[chassis_id] = {
                    "chassis_id": curr_chassis["Id"],
                    "chassis_type": curr_chassis["ChassisType"],
                    "manufacturer": curr_chassis["Manufacturer"],
                    "model": curr_chassis["Model"],
                    "health": curr_chassis["Status"]["Health"] or "NA",
                    "state": curr_chassis["Status"]["State"],
                }
            redfish_obj.logout()
        logger.info("Chassis data: %s", chassis_data)
        return chassis_data

    def get_storage_drive_data(self) -> Tuple[Dict[str, int], Dict[str, List]]:
        """Return storage drive data and count.

        Returns:
            storage_drive_count: Dict of system ids mapped to the total number
            of storage drives on that system.
            storage_drive_data: Dict of system ids mapped to list of storage
            drives on that system.
        """
        storage_drive_data: Dict[str, List] = {}
        # storage drives on each system
        storage_drive_count: Dict[str, int] = {}
        storage_root_uri_pattern = "/redfish/v1/Systems/{}/Storage"
        redfish_obj: Optional[HttpClient] = self._get_redfish_obj()

        if redfish_obj:
            try:
                system_ids: List[str] = redfish_utilities.systems.get_system_ids(redfish_obj)
            except redfish_utilities.systems.RedfishSystemNotFoundError:
                logger.info("No system instances found.")
                return storage_drive_count, storage_drive_data

            for system_id in system_ids:
                storage_drive_count[system_id] = 0

                storage_ids: List[str] = redfish_utilities.collections.get_collection_ids(
                    redfish_obj, storage_root_uri_pattern.format(system_id)
                )
                storage_drive_data_in_curr_system: List[Dict] = []
                for storage_id in storage_ids:
                    # /redfish/v1/Systems/1/Storage/XYZ123/
                    curr_storage_uri = (
                        storage_root_uri_pattern.format(system_id) + "/" + storage_id
                    )
                    # list of storage drives for that storage id
                    storage_drives_list: List[Dict] = redfish_obj.get(curr_storage_uri).dict[
                        "Drives"
                    ]
                    storage_drive_count[system_id] += len(storage_drives_list)

                    storage_drive_uris: List[str] = [
                        storage_drive["@odata.id"] for storage_drive in storage_drives_list
                    ]

                    for uri in storage_drive_uris:
                        data = redfish_obj.get(uri).dict
                        storage_drive_data_in_curr_system.append(
                            {
                                "storage_id": storage_id,
                                "drive_id": data["Id"],
                                "state": data["Status"]["State"],
                                "health": data["Status"]["Health"] or "NA",
                            }
                        )

                storage_drive_data[system_id] = storage_drive_data_in_curr_system

            redfish_obj.logout()

        logger.info("storage drive count: %s", storage_drive_count)
        logger.info("storage drive data: %s", storage_drive_data)
        return storage_drive_count, storage_drive_data

    def get_memory_dimm_data(self) -> Tuple[Dict[str, int], Dict[str, List]]:
        """Return memory dimm data and count.

        Returns:
            memory_dimm_count: Dict of system ids mapped to the total number
            of memory dimms on that system.
            memory_dimm_data: Dict of system ids mapped to list of memory dimms
            on that system.
        """
        memory_dimm_data: Dict[str, List] = {}
        memory_dimm_count: Dict[str, int] = {}
        memory_dimm_uris: List[str] = []
        memory_root_uri_pattern = "/redfish/v1/Systems/{}/Memory"
        redfish_obj: Optional[HttpClient] = self._get_redfish_obj()

        if redfish_obj:
            try:
                system_ids: List[str] = redfish_utilities.systems.get_system_ids(redfish_obj)
            except redfish_utilities.systems.RedfishSystemNotFoundError:
                logger.info("No system instances found.")
                return memory_dimm_count, memory_dimm_data

            for system_id in system_ids:
                # /redfish/v1/Systems/1/Memory
                memory_root_uri = memory_root_uri_pattern.format(system_id)
                curr_memory_data: Dict[str, Any] = redfish_obj.get(memory_root_uri).dict
                for member in curr_memory_data["Members"]:
                    memory_dimm_uris.append(member["@odata.id"])
                memory_dimm_count[system_id] = len(memory_dimm_uris)
                memory_dimm_data_in_curr_system: List[Dict] = []
                for memory_dimm_uri in memory_dimm_uris:
                    # /redfish/v1/Systems/1/Memory/{proc1dimm1, proc1dimm2...}
                    memory_dimm: Dict[str, Any] = redfish_obj.get(memory_dimm_uri).dict
                    memory_dimm_data_in_curr_system.append(
                        {
                            "memory_id": memory_dimm["Id"],
                            "health": memory_dimm["Status"]["Health"] or "NA",
                            "state": memory_dimm["Status"]["State"],
                        }
                    )
                memory_dimm_data[system_id] = memory_dimm_data_in_curr_system
            redfish_obj.logout()

        logger.info("memory dimm count: %s", memory_dimm_count)
        logger.info("memory dimm data: %s", memory_dimm_data)
        return memory_dimm_count, memory_dimm_data

    def get_smart_storage_health_data(self) -> Dict[str, Any]:
        """Return Smart Storage health data if present on the chassis.

        Returns a dict of chassis ids mapped to the smart storage health data on that chassis.
        """
        smart_storage_health_data: Dict[str, Any] = {}
        redfish_obj: Optional[HttpClient] = self._get_redfish_obj()
        smart_storage_root_uri_pattern = "/redfish/v1/Chassis/{}/SmartStorage"

        if redfish_obj:
            try:
                chassis_ids: List[str] = redfish_utilities.inventory.get_chassis_ids(redfish_obj)
            except redfish_utilities.inventory.RedfishChassisNotFoundError:
                logger.info("No chassis instances found.")
                return smart_storage_health_data

            for chassis_id in chassis_ids:
                smart_storage_uri = smart_storage_root_uri_pattern.format(chassis_id)
                smart_storage_data: Optional[Dict[str, Any]] = self._verify_redfish_call(
                    redfish_obj, smart_storage_uri
                )
                if not smart_storage_data:
                    logger.info(
                        "Smart Storage URI endpoint not found for chassis ID: %s", chassis_id
                    )
                    break
                smart_storage_health_data[chassis_id] = {
                    "health": smart_storage_data["Status"]["Health"] or "NA",
                }

            redfish_obj.logout()
        logger.info("smart storage health data: %s", smart_storage_health_data)
        return smart_storage_health_data

    def get_discover(self, ttl: int) -> Callable:
        """Return the cached discover function.

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
            logger.info("Discovered redfish services: %s", services)
            return True

        return _discover
