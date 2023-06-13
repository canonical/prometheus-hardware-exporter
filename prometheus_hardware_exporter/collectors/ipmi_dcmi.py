"""IPMI DCMI metrics collector."""

import re
from logging import getLogger
from typing import Dict

from ..utils import Command

logger = getLogger(__name__)

CURRENT_POWER_REGEX = re.compile(r"^Current Power\s*:\s*(?P<value>[0-9.]*)\s*Watts.*")


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
