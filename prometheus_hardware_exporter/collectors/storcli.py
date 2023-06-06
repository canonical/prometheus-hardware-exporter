"""Collector for MegaRAID controller."""

import re
from logging import getLogger
from typing import Any, Dict, List

from ..utils import Command

logger = getLogger(__name__)


CACHE_REGEX = re.compile(r'"Cache"\s*:\s*"(\w*)"')
CONTROLLER_CNT_REGEX = re.compile(r'"Controller Count"\s*:\s*(?P<num>\d*)')
DG_VD_REGEX = re.compile(r'"DG\/VD"\s*:\s*"(\d*)\/(\d*)"')
HOSTENAME_REGEX = re.compile(r'"Host Name"\s*:\s*"(?P<hostname>\w*)"')
NUM_CONTROLLER_REGEX = re.compile(r'"Number of Controllers"\s*:\s*(?P<num>\d*)')
STATE_REGEX = re.compile(r'"State"\s*:\s*"(\w*)"')


class StorCLI(Command):
    """Command line tool for MegaRAID Controller."""

    prefix = ""
    command = "storcli"

    def _get_all_virtual_drives(self, controller: int) -> List[Dict[str, str]]:
        """Get all virtual drive information in this controller.

        Equivalent to running `storcli /cx/vall show all` for controller "x".

        Returns:
            payloads: list of virtual drives information or []
        """
        result = self(f"/c{controller}/vall show J")
        if result.error:
            logger.error(result.error)
            return []

        dg_vd_matches = DG_VD_REGEX.findall(result.data)
        state_matches = STATE_REGEX.findall(result.data)
        cache_matches = CACHE_REGEX.findall(result.data)
        if not all([dg_vd_matches, state_matches, cache_matches]):
            logger.error("Controller %d: cannot get virtual drive information.", controller)
            return []

        payloads = []
        for ctrl_id, virtual_device, state, cache in zip(
            [i[0] for i in dg_vd_matches],
            [i[1] for i in dg_vd_matches],
            state_matches,
            cache_matches,
        ):
            payloads.append(
                {
                    "DG": ctrl_id,
                    "VD": virtual_device,
                    "state": state,
                    "cache": cache,
                }
            )
        return payloads

    def _get_controller_ids(self) -> List[int]:
        """Get controller ids.

        Returns:
            ids: list of controller ids or []
        """
        result = self("show ctrlcount J")
        if result.error:
            logger.error(result.error)
            return []

        ctrl_count_match = CONTROLLER_CNT_REGEX.search(result.data)
        if not ctrl_count_match:
            logger.error("Cannot get controller ids.")
            return []

        return list(range(int(ctrl_count_match.group("num"))))

    def get_controllers(self) -> Dict[str, Any]:
        """Get the number of controller.

        Returns:
            payload: a dictionary of controller count and hostname, or {}
        """
        result = self("show all J")
        if result.error:
            logger.error(result.error)
            return {}

        num_match = NUM_CONTROLLER_REGEX.search(result.data)
        hostname_match = HOSTENAME_REGEX.search(result.data)
        if not all([num_match, hostname_match]):
            logger.error("Cannot get controller's information.")
            return {}

        payload = {
            "count": int(num_match.group("num")) if num_match else 0,
            "hostname": hostname_match.group("hostname") if hostname_match else "",
        }
        return payload

    def get_all_virtual_drives(
        self,
    ) -> Dict[int, List[Dict[str, str]]]:
        """Get all virtual drive information.

        Equivalent to running `storcli /cx/vall show all` for all controller "x".

        Returns:
            virtual_drives: dictionary of all virtual drive information or {}
        """
        ids = self._get_controller_ids()
        if not ids:
            return {}

        payload = {}
        for controller_id in ids:
            vd_payload = self._get_all_virtual_drives(controller_id)
            if not vd_payload:
                return {}
            payload[controller_id] = vd_payload
        return payload
