"""Lshw metrics collector."""
import json
from logging import getLogger
from typing import Dict, List

from ..utils import Command

logger = getLogger(__name__)


class LSHW(Command):
    """Command line tool for lshw."""

    prefix = ""
    command = "lshw"

    def get_powers(self) -> List[Dict[str, str]]:
        """Get power class data."""
        result = self("-c power -json")
        if result.error:
            logger.error(result.error)
            return []
        data = json.loads(result.data)
        return data

    def get_power_capacities(self) -> List[int]:
        """Get list of power capacities."""
        powers = self.get_powers()
        capacities = []
        for power in powers:
            capacities.append(int(power.get("capacity", 0)))
        return capacities
