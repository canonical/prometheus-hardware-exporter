"""IPMI SEL metrics collector."""

from logging import getLogger
from typing import Dict, List

from ..utils import Command

logger = getLogger(__name__)


class IpmiSel(Command):
    """Command line tool for ipmi sel."""

    prefix = "sudo"
    command = "ipmi-sel"

    def get_sel_entries(self) -> List[Dict[str, str]]:
        """Get SEL entries along with state.

        Returns:
            sel_entries: a list of dictionaries containing sel_sentries, or []
        """
        result = self("--output-event-state --interpret-oem-data --entity-sensor-names")
        if result.error:
            logger.error(result.error)
            return []

        raw_sel_data = result.data.strip().split("\n")
        sel_entries = []
        sel_data_fields = ["ID", "Date", "Time", "Name", "Type", "State", "Event"]
        for sel_item in raw_sel_data[1:]:
            sel_item_values = sel_item.split("|")
            sel_item_values = [entry.strip() for entry in sel_item_values]
            sel_entries.append(dict(zip(sel_data_fields, sel_item_values)))
        return sel_entries
