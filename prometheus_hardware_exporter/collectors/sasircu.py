"""Collector for LSI SAS controllers."""

import re
from collections import defaultdict
from logging import getLogger
from typing import Any, Dict, List, Set, Tuple

from prometheus_hardware_exporter.config import Config

from ..utils import Command

logger = getLogger(__name__)

SECTIONS_REGEX = re.compile(
    r"(?<=^Controller information\n)"
    r"-+\n"
    r"(?P<ctrl>(?:.|\n)*)"
    r"^-+\n"
    r"^IR Volume information\n"
    r"-+\n"
    r"(?P<vols>(?:.|\n)*)"
    r"^-+\n"
    r"^Physical device information\n"
    r"-+\n"
    r"(?P<disks>(?:.|\n)*)"
    r"^-+\n"
    r"^Enclosure information\n"
    r"-+\n"
    r"(?P<encl>(?:.|\n)*)"
    r"^-+\n",
    re.MULTILINE,
)
VOLS_REGEX = re.compile(
    r"^IR volume (?P<n>\d+)\n"
    r"(?P<kv_data>(?:.|\n)*?)"
    r"\s+Physical hard disks\s+:.*\n"
    r"(?P<topology>(?:^\s+PHY.*\n)+)",
    re.MULTILINE,
)
DISKS_REGEX = re.compile(
    r"(?<=^Device is a Hard disk\n)(?P<kv_data>(?:.|\n)*?)(?=^$)", re.MULTILINE
)
VOL_TOPOLOGY_REGEX = re.compile(
    r"\s+PHY\[(?P<n>\d+)\]\s+Enclosure#\/Slot#\s+:\s+(?P<enc>\d+):(?P<slot>\d+)"
)

ADAPTERS_REGEX = re.compile(
    r"-\s*\n\s*(?P<adapters>(?:.|\n)*)SAS[2,3]IRCU: Utility Completed Successfully"
)


class Sasircu(Command):
    """Command line tool for LSI SAS Controller."""

    prefix = ""
    command = ""

    def __init__(self, config: Config, version: int) -> None:
        """Initialize the command line tool."""
        self.version = version
        self.command = f"sas{version}ircu"
        super().__init__(config)

    def _parse_key_value(self, text: str) -> Dict[str, Any]:
        """Return a dictionary from a text with the format of "key : value".

        For example:

        text = '''
        key1 : value1
        key2 : value2
        key3 : value3
        '''

        _parse_key_value(text) returns {"key1": "value1", "key2": "value2"}

        Returns:
            dict: key value pairs.
        """
        lines = [line.strip() for line in text.strip().split("\n")]
        kv_regex = re.compile(r"\s*(?P<k>.*?)\s+:\s+(?P<v>.*)")
        data = {}
        for line in lines:
            match = kv_regex.search(line)
            if not match:
                return {}
            data[match.group("k")] = match.group("v")
        return data

    def _get_controller(self, text: str) -> Dict[str, str]:
        """Return controller information from the controller section text.

        Returns:
            Controller information
        """
        controller = self._parse_key_value(text)

        if not controller:
            logger.warning("Cannot parse controller information or missing controller.")

        return controller

    def _get_ir_volumes(self, text: str) -> Dict[str, Any]:
        """Return IR volumes information from the IR volume section text.

        Returns:
            IR volume information
        """
        volumes = {}
        for vol_id, vol_kv_text, vol_topology in VOLS_REGEX.findall(text):
            topology = {}
            for member_id, enclosure_id, slot_id in VOL_TOPOLOGY_REGEX.findall(vol_topology):
                topology[f"PHY[{member_id}] Enclosure#/Slot#"] = f"{enclosure_id}:{slot_id}"
            volumes[vol_id] = {
                **self._parse_key_value(vol_kv_text),
                "Physical hard disks": topology,
            }

        if not volumes:
            logger.warning("Cannot parse IR volumes information or missing IR volumes.")

        return volumes

    def _get_physical_disks(self, text: str) -> Dict[str, Dict[str, str]]:
        """Return physical disks information from the physical disk section text.

        Returns:
            Physical disk information
        """
        topology = {}
        for match in DISKS_REGEX.findall(text):
            disk = self._parse_key_value(match)
            encl = disk["Enclosure #"]
            slot = disk["Slot #"]
            topology[f"{encl}:{slot}"] = disk

        if not topology:
            logger.warning("Cannot parse physical disks information.")

        return topology

    def _get_enclosures(self, text: str) -> Dict[str, Dict[str, str]]:
        """Return enclosures information from the enclosure section text.

        Returns:
            Enclosures information
        """
        enclosures: Dict[str, Dict[str, str]] = {}

        encl = defaultdict(list)
        for line in text.strip().split("\n"):
            data = line.strip().split(":", 1)
            if len(data) != 2:
                enclosures = {}
                break
            encl[data[0].strip()].append(data[1].strip())

        keys = list(encl.keys())
        values = list(zip(*encl.values()))
        for value in values:
            encl_idx = value[0]
            enclosures[encl_idx] = dict(zip(keys, value))

        if not enclosures:
            logger.warning("Cannot parse enclosures information or missing enclosures.")

        return enclosures

    def get_adapters(self) -> Dict[str, Dict[str, str]]:
        """Get information about all available LSI adapters.

        Returns:
            adapters: dictionary of adapter information keyed by adapter index
        """
        result = self("list")
        if result.error:
            logger.error(result.error)
            return {}

        adapters_match = ADAPTERS_REGEX.search(result.data)
        if not adapters_match:
            logger.error("Cannot find LSI SAS %d adapters.", self.version)
            return {}

        adapters = {}
        adapter_headers = [
            "Index",
            "Adapter Type",
            "Vendor ID",
            "Device ID",
            "Pci Address",
            "SubSys Ven ID",
            "SubSys Dev ID",
        ]
        for adapter in adapters_match.group("adapters").strip().split("\n"):
            adapter_content = adapter.strip().split()
            adapters[adapter_content[0]] = dict(zip(adapter_headers, adapter_content))

        return adapters

    def get_all_information(self, controller_id: str) -> Dict[str, Any]:
        """Get controller, volume, and physical device info.

        Returns:
            controller, volume, and physical device as a dictionary
        """
        result = self(f"{controller_id} DISPLAY")
        if result.error:
            logger.error(result.error)
            return {}

        match = SECTIONS_REGEX.search(result.data)
        if not match:
            logger.error("Cannot get information about controller, volume, and physical devices.")
            return {}

        sections = match.groupdict()
        information = {
            "controller": self._get_controller(sections["ctrl"]),
            "ir_volumes": self._get_ir_volumes(sections["vols"]),
            "enclosures": self._get_enclosures(sections["encl"]),
            "physical_disks": self._get_physical_disks(sections["disks"]),
        }

        return information


class LSISASCollectorHelper:
    """Helper class to generate payloads."""

    def count_ir_volume_state(
        self, ir_volumes: List[Dict[str, str]], state: Set
    ) -> Tuple[int, int, int]:
        """Count the number of ir volume in a particular state."""
        ready_ir_volumes = 0
        unready_ir_volumes = 0
        for ir_volume in ir_volumes:
            ready = ir_volume["status"] in state
            ready_ir_volumes += ready
            unready_ir_volumes += not ready
        return ready_ir_volumes + unready_ir_volumes, ready_ir_volumes, unready_ir_volumes

    def count_physical_disk_state(
        self, physical_disks: List[Dict[str, str]], state: Set
    ) -> Tuple[int, int, int]:
        """Count the number of physical disk in a particular set of state."""
        ready_disks = 0
        unready_disks = 0
        for physical_disk in physical_disks:
            ready = physical_disk["state"] in state
            ready_disks += ready
            unready_disks += not ready
        return ready_disks + unready_disks, ready_disks, unready_disks

    def extract_enclosures(self, idx: str, info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract the enclosures payloads."""
        data = []
        for encl in info["enclosures"].values():
            data.append(
                {
                    "controller_id": idx,
                    "enclosure_id": encl["Enclosure#"],
                    "num_slots": encl["Numslots"],
                    "start_slot": encl["StartSlot"],
                }
            )
        return data

    def extract_ir_volumes(self, idx: str, info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract the ir volumes payloads."""
        data = []
        for volume in info["ir_volumes"].values():
            data.append(
                {
                    "controller_id": idx,
                    "volume_id": volume["Volume ID"],
                    "status": volume["Status of volume"],
                    "size_mb": volume["Size (in MB)"],
                    "boot": volume["Boot"],
                    "raid_level": volume["RAID level"],
                    "hard_disk": ",".join(volume["Physical hard disks"].values()),
                }
            )
        return data

    def extract_physical_disks(self, idx: str, info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract the physical disks payloads."""
        data = []
        for disk in info["physical_disks"].values():
            data.append(
                {
                    "controller_id": idx,
                    "enclosure_id": disk["Enclosure #"],
                    "slot_id": disk["Slot #"],
                    "size_mb_sectors": disk["Size (in MB)/(in sectors)"],
                    "drive_type": disk["Drive Type"],
                    "protocol": disk["Protocol"],
                    "state": disk["State"],
                }
            )
        return data
