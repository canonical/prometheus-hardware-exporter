"""Collector for PowerEdgeRAID controller."""

from logging import getLogger
from typing import Any, Dict, List, Union

from ..utils import Command, get_json_output

logger = getLogger(__name__)


class PercCLI(Command):
    """Command line tool for PowerEdge RAID Controller."""

    prefix = ""
    command = "perccli"

    def _get_controllers(self) -> Union[dict, Exception]:
        result = self("/call show j")
        if result.error:
            logger.error(result.error)
            return result.error
        return get_json_output(result.data)

    def _cmd_status(self, controller: Dict[str, Any]) -> bool:
        return controller["Command Status"]["Status"] == "Success"

    def _ctrl_exists(self, controllers: Dict[str, Any]) -> bool:
        """Check if the output json like the example output.

        Example output:
            {
              "Controllers": [
                {
                  "Command Status": {
                    "CLI Version": "007.1020.0000.0000 July 1, 2019",
                    "Operating system": "Linux 5.15.0-71-generic",
                    "Status": "Failure",
                    "Description": "No Controller found"
                  }
                }
              ]
            }
        """
        cmd_status = controllers["Controllers"][0]["Command Status"]
        if (
            cmd_status["Status"] == "Failure"
            and cmd_status["Description"] == "No Controller found"
        ):
            return False
        return True

    def _get_ctrl_id(self, controller: Dict[str, Any]) -> int:
        return controller["Command Status"]["Controller"]

    def success(self) -> bool:
        """Return false if command fail."""
        result = self._get_controllers()
        if isinstance(result, Exception):
            logger.error(result)
            return False
        return True

    def ctrl_exists(self) -> bool:
        """Check if controller exists."""
        result = self._get_controllers()
        if isinstance(result, Exception):
            logger.error(result)
            return False

        if self._ctrl_exists(result):
            return True
        return False

    def ctrl_successes(self) -> Dict[int, bool]:
        """Get each controller's cmd success."""
        result = self._get_controllers()
        if isinstance(result, Exception):
            logger.error(result)
            return {}

        if not self._ctrl_exists(result):
            return {}

        payload = {}
        for controller in result.get("Controllers", []):
            success = self._cmd_status(controller)
            ctrl_id = self._get_ctrl_id(controller)
            payload[ctrl_id] = success
        return payload

    def get_controllers(self) -> Dict[str, Any]:
        """Get the number of controller.

        Returns:
            payload: a dictionary of controller count or {}
        """
        result = self._get_controllers()
        if isinstance(result, Exception):
            logger.error(result)
            return {}

        controller_count = 0 if not self._ctrl_exists(result) else len(result["Controllers"])

        return {
            "count": controller_count,
        }

    def get_virtual_drives(self) -> Dict[int, List[Dict[str, Any]]]:
        """Get all virtual drive information.

        Returns:
            virtual_drives: dictionary of all virtual drive information or {}
        """
        result = self._get_controllers()
        if isinstance(result, Exception):
            logger.error(result)
            return {}

        payload = {}
        for controller in result["Controllers"]:
            if self._cmd_status(controller):
                ctrl_id = self._get_ctrl_id(controller)
                vd_payloads = []
                for virtual_device in controller["Response Data"].get("VD LIST", []):
                    device_group, virtual_disk = virtual_device["DG/VD"].split("/")
                    state = virtual_device["State"]
                    cache = virtual_device["Cache"]
                    vd_payloads.append(
                        {
                            "DG": device_group,
                            "VD": virtual_disk,
                            "state": state,
                            "cache": cache,
                        }
                    )
                payload[ctrl_id] = vd_payloads
        return payload

    def get_physical_devices(self) -> Dict[int, List[Dict[str, Any]]]:
        """Get all physical device information.

        Returns:
            physical_devices: dictionary of all physical device information or {}
        """
        result = self._get_controllers()
        if isinstance(result, Exception):
            logger.error(result)
            return {}
        payload = {}
        for ctrl in result["Controllers"]:
            if self._cmd_status(ctrl):
                ctrl_id = self._get_ctrl_id(ctrl)
                pd_payloads = []
                for physical_device in ctrl["Response Data"].get("PD LIST", []):
                    eid, slt = physical_device["EID:Slt"].split(":")
                    pd_payloads.append(
                        {
                            "eid": eid,
                            "slt": slt,
                            "state": physical_device["State"],
                            "DG": physical_device["DG"],
                            "size": physical_device["Size"],
                            "media_type": physical_device["Med"],
                        }
                    )
                payload[ctrl_id] = pd_payloads
        return payload
