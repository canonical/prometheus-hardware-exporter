"""Dmidecode metrics collector."""

import re
from functools import lru_cache
from logging import getLogger
from typing import List

from ..utils import Command

logger = getLogger(__name__)


MAX_POWER_CAPACITY_REGEX = r"(Max Power Capacity: )(\d+)( W)"


class Dmidecode(Command):
    """Command line tool for dmidecode."""

    prefix = ""
    command = "dmidecode"

    @lru_cache  # PSU ratings won't change over the lifetime of a server
    def get_power_capacities(self) -> List[int]:
        """Get list of power capacities."""
        result = self("-t 39")
        if result.error:
            logger.error(result.error)
            return []

        lines = re.findall(MAX_POWER_CAPACITY_REGEX, result.data)
        powers = []
        for line in lines:
            powers.append(int(line[1]))
        return powers
