"""IPMI DCMI metrics collector."""

import re
from logging import getLogger
from typing import Dict, Optional, Tuple

from ..utils import Command

logger = getLogger(__name__)

CURRENT_POWER_REGEX = re.compile(r"^Current Power\s*:\s*(?P<value>[0-9.]*)\s*Watts.*")


class IpmiTool(Command):
    """Command line tool for ipmitool."""

    prefix = ""
    command = "ipmitool"

    def get_ps_redundancy(self) -> Tuple[bool, bool]:
        """Get power supply redundancy.

        returns:
            - ok - True if fetching redundancy info is successful
            - redundancy - True if redundancy is enabled
        """
        result = self("""sdr type "Power Supply" -c""")
        if result.error:
            logger.error(result.error)
            return False, False
        output = []
        for line in result.data.splitlines():
            data = line.split(",")
            if "Redundancy" in data[0]:
                # column 4 is redundancy status
                output.append(data[4])
        return True, all(status == "Fully Redundant" for status in output) | False

    def get_ipmi_host(self) -> Optional[str]:
        """Get IPMI host name.

        returns:
            hostname - IPMI/BMC host or None
        """
        result = self("lan print")
        if result.error:
            logger.error(result.error)
            return None
        for line in result.data.splitlines():
            if "IP Address" in line and "Source" not in line:
                _, ip_address = line.split(":", 1)
                return ip_address.strip()
        return None


class IpmiDcmi(Command):
    """Command line tool for ipmi dcmi."""

    prefix = ""
    command = "ipmi-dcmi"

    def get_current_power(self) -> Dict[str, float]:
        """Get current power measurement in Watts.

        Returns:
            payload: a dictionary containing current_power, or {}
        """
        result = self("--get-system-power-statistics")
        if result.error:
            logger.error(result.error)
            return {}

        try:
            current_power = CURRENT_POWER_REGEX.findall(result.data)[0]
        except IndexError:
            logger.error("Cannot get current power.")
            return {}
        payload = {"current_power": float(current_power)}
        return payload
