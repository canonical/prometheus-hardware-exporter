"""Collector for HP Storage Array."""

import re
from logging import getLogger
from typing import Dict, List

from ..utils import Command

logger = getLogger(__name__)


class SsaCLI(Command):
    """Command line tool for HP Storage Controller."""

    prefix = ""
    command = "ssacli"

    def get_payload(self) -> Dict[str, Dict]:
        """Get status of all controllers, logical drives and physical drives.

        Returns:
            payload: a dictionary where key, value pair is slot, controller information pair
            in the following format:
            {
                "slot": {"controller_status": controller_status,
                "ld_status": ld_status,
                "pd_status": pd_status
                }
            }
        """
        slots = self._get_controller_slots()
        payload = {}
        for slot in slots:
            controller_status = self._get_controller_status(slot)
            ld_status = self._get_ld_status(slot)
            pd_status = self._get_pd_status(slot)
            payload[slot] = {
                "controller_status": controller_status,
                "ld_status": ld_status,
                "pd_status": pd_status,
            }
        return payload

    def _get_controller_slots(self) -> List[str]:
        """Get the controller slots(s) available for probing.

        Returns:
            slots: List of slots where HP storage controllers are available, or []
        """
        result = self("ctrl all show")
        if result.error:
            logger.error(result.error)
            return []

        controllers_raw = result.data.strip().split("\n")
        slots = []
        for controller in controllers_raw:
            if "in Slot" in controller:
                slots.append(controller.split()[5])
        return slots

    def _get_controller_status(self, slot: str) -> Dict[str, str]:
        """Get controller status for each part of the controller.

        Returns:
            ctrl_status: dict where each item is part, status pair for the controller.
        """
        result = self(f"ctrl slot={slot} show status")
        if result.error:
            logger.error(result.error)
            return {}

        ctrl_status = {}
        for line in result.data.splitlines():
            line = line.strip()
            if (not line) or line.startswith("Smart Array") or line.startswith("Smart HBA"):
                continue
            if ":" not in line:
                err = f"Unrecognised line for controller '{line}'"
                logger.warning(err)
                continue
            part, status = line.split(":")
            ctrl_status[part] = status
        return ctrl_status

    def _get_ld_status(self, slot: str) -> Dict[str, str]:
        """Get logical drives status.

        Returns:
            ld_status: dict where each item is drive_id, status pair.
        """
        result = self(f"ctrl slot={slot} ld all show status")
        if result.error:
            logger.error(result.error)
            return {}

        innocuous_errors = re.compile(
            r"^Error: The specified (device|controller) does not have any logical"
        )
        drive_status_line = re.compile(r"^\s*logicaldrive")

        ld_status = {}
        for line in result.data.splitlines():
            line = line.strip()
            if not line or innocuous_errors.search(line) or not drive_status_line.search(line):
                continue
            drive_id = line.split()[1]
            status = line.split("):")[1].lstrip().upper()
            ld_status[drive_id] = status

        return ld_status

    def _get_pd_status(self, slot: str) -> Dict[str, str]:
        """Get physical drives status.

        Returns:
            pd_status: dict where each item is drive_id, status pair.
        """
        result = self(f"ctrl slot={slot} pd all show status")
        if result.error:
            logger.error(result.error)
            return {}

        innocuous_errors = re.compile(
            r"^Error: The specified (device|controller) does not have any physical"
        )
        drive_status_line = re.compile(r"^\s*physicaldrive")
        pd_status = {}
        for line in result.data.splitlines():
            line = line.strip()
            if not line or innocuous_errors.search(line) or not drive_status_line.search(line):
                continue
            drive_id = line.split()[1]
            status = line.split("):")[1].lstrip().upper()
            pd_status[drive_id] = status

        return pd_status
