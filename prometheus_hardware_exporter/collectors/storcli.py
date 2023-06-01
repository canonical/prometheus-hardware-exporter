"""Collector for MegaRAID controller."""

import re
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple

from ..utils import Command

logger = getLogger(__name__)


class StorCLI(Command):
    """Command line tool for MegaRAID Controller."""

    prefix = ""
    command = "storcli"
    installed = False

    def _get_all_virtual_drives(
        self, controller: int
    ) -> Tuple[Optional[List[Dict[str, str]]], Optional[Exception]]:
        """Get all virtual drive information in this controller.

        Equivalent to running `storcli /cx/vall show all` for controller "x".

        Returns:
            virtual_drive: dictionary of a virtual drive information or None
            error: an exception if there is any or None
        """
        result, error = self(f"/c{controller}/vall show J")
        if error:
            return None, error

        dg_vd_regex = re.compile(r'"DG\/VD"\s*:\s*"(\d*)\/(\d*)"')
        state_regex = re.compile(r'"State"\s*:\s*"(\w*)"')
        cache_regex = re.compile(r'"Cache"\s*:\s*"(\w*)"')
        dg_vd_matches = dg_vd_regex.findall(result)  # type: ignore[arg-type]
        state_matches = state_regex.findall(result)  # type: ignore[arg-type]
        cache_matches = cache_regex.findall(result)  # type: ignore[arg-type]
        if not all([dg_vd_matches, state_matches, cache_matches]):
            return None, ValueError(
                f"Controller {controller}: cannot get virtual drive information."
            )

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
        return payloads, None

    def _get_controller_ids(self) -> Tuple[Optional[List[int]], Optional[Exception]]:
        """Get controller ids.

        Returns:
            ids: list of controller ids, or None
            error: an exception if there is any, or None
        """
        result, error = self("show ctrlcount J")
        if error:
            return None, ValueError("Cannot get controller ids.")

        num_controller_regex = re.compile(r'"Controller Count"\s*:\s*(?P<num>\d*)')
        num_match = num_controller_regex.search(result)  # type: ignore[arg-type]
        if not num_match:
            error_msg = "Cannot get the number of controllers."
            return None, ValueError(error_msg)

        return list(range(int(num_match.group("num")))), None

    def get_controllers(self) -> Tuple[Optional[Dict[str, Any]], Optional[Exception]]:
        """Get the number of controller.

        Returns:
            payload: a dictionary of number of controller and hostname, or None
            error: an exception if there is any, or None
        """
        result, error = self("show all J")
        if error:
            logger.error("Cannot get the number of controllers.")
            return None, error

        num_controller_regex = re.compile(r'"Number of Controllers"\s*:\s*(?P<num>\d*)')
        hostename_regex = re.compile(r'"Host Name"\s*:\s*"(?P<hostname>\w*)"')
        num_match = num_controller_regex.search(result)  # type: ignore[arg-type]
        hostname_match = hostename_regex.search(result)  # type: ignore[arg-type]
        if not all([num_match, hostname_match]):
            error_msg = "Cannot get controller's information."
            logger.error(error_msg)
            return None, ValueError(error_msg)

        payload = {
            "count": int(num_match.group("num")),  # type: ignore[union-attr]
            "hostname": hostname_match.group("hostname"),  # type: ignore[union-attr]
        }
        return payload, None

    def get_all_virtual_drives(
        self,
    ) -> Tuple[Optional[Dict[int, Optional[List[Dict[str, str]]]]], Optional[Exception]]:
        """Get all virtual drive information.

        Equivalent to running `storcli /cx/vall show all` for all controller "x".

        Returns:
            virtual_drives: dictionary of all virtual drive information or None
            error: an exception if there is any or None
        """
        ids, error = self._get_controller_ids()
        if error:
            logger.error(str(error))
            return None, error

        payload = {}
        if ids:
            for controller_id in ids:
                vd_payload, error = self._get_all_virtual_drives(controller_id)
                if error:
                    logger.error(str(error))
                    return None, error
                payload[controller_id] = vd_payload
        return payload, None
