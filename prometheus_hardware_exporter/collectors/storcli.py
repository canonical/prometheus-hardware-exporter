"""Collector for MegaRAID controller."""

import json
from logging import getLogger
from typing import Any, Dict, List, Set, Tuple

from ..utils import Command

logger = getLogger(__name__)


class StorCLI(Command):
    """Command line tool for MegaRAID Controller."""

    prefix = ""
    command = "storcli"

    def _extract_enclosures(
        self, response: Dict[str, List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """Get all enclosures information in this controller.

        Returns:
            payloads: list of enclosures information or []
        """
        if "Enclosure LIST" not in response:
            logger.error("Cannot enclosure information.")
            return []
        return response["Enclosure LIST"]

    def _extract_virtual_drives(
        self, response: Dict[str, List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """Get all virtual drives information in this controller.

        Returns:
            payloads: list of virtual drives information or []
        """
        if "VD LIST" not in response:
            logger.error("Cannot virtual drive information.")
            return []
        return response["VD LIST"]

    def _extract_physical_drives(
        self, response: Dict[str, List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """Get all physical drives information in this controller.

        Returns:
            payloads: list of physical drives information or []
        """
        if "PD LIST" not in response:
            logger.error("Cannot physical drive information.")
            return []
        return response["PD LIST"]

    def get_all_information(self) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
        """Get the information about all controllers.

        Returns:
            An extracted output of `storcli /cALL show all J`
        """
        result = self("/cALL show all J")
        if result.error:
            logger.error(result.error)
            return {}

        data = json.loads(result.data)["Controllers"]

        final_output: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
        for controller in data:
            if "Response Data" not in controller:
                logger.error("Cannot get controller information.")
                continue
            response = controller["Response Data"]
            idx = response["Basics"]["Controller"]
            final_output[idx] = {
                "enclosures": self._extract_enclosures(response),
                "virtual_drives": self._extract_virtual_drives(response),
                "physical_drives": self._extract_physical_drives(response),
            }
        return final_output


class MegaRAIDCollectorHelper:
    """Helper class to generate payloads."""

    def count_virtual_drive_state(
        self, virtual_drives: List[Dict[str, str]], state: Set
    ) -> Tuple[int, int, int]:
        """Count the number of virtual drive in a particular state."""
        ready_virtual_drives = 0
        unready_virtual_drives = 0
        for virtual_drive in virtual_drives:
            ready = virtual_drive["state"] in state
            ready_virtual_drives += ready
            unready_virtual_drives += not ready
        return (
            ready_virtual_drives + unready_virtual_drives,
            ready_virtual_drives,
            unready_virtual_drives,
        )

    def extract_enclosures(
        self, idx: str, enclosures: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract the enclosures payloads."""
        data = []
        for encl in enclosures:
            data.append(
                {
                    "controller_id": idx,
                    "enclosure_id": str(encl["EID"]),
                    "num_slots": str(encl["Slots"]),
                    "state": encl["State"],
                }
            )
        return data

    def extract_virtual_drives(
        self, idx: str, virtual_drives: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract the virtual drives payloads."""
        data = []
        for virtual_drive in virtual_drives:
            dg_vd = virtual_drive["DG/VD"].split("/")
            drive_group = str(dg_vd[0])
            virtual_drive_group = str(dg_vd[1])
            data.append(
                {
                    "controller_id": idx,
                    "drive_group": drive_group,
                    "virtual_drive_group": virtual_drive_group,
                    "state": virtual_drive["State"],
                    "raid_level": virtual_drive["TYPE"],
                    "name": virtual_drive["Name"],
                }
            )
        return data

    def extract_physical_drives(
        self, idx: str, physical_drives: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract the physical drives payloads."""
        data = []
        for physical_drive in physical_drives:
            eid_slt = physical_drive["EID:Slt"].split(":")
            slot_id = str(eid_slt[1])
            enclosure_id = str(eid_slt[0])
            data.append(
                {
                    "controller_id": idx,
                    "enclosure_id": enclosure_id,
                    "slot_id": slot_id,
                    "state": physical_drive["State"],
                    "drive_type": physical_drive["Med"],
                }
            )
        return data
