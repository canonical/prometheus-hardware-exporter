"""IPMI SEL metrics collector."""

import datetime
from logging import getLogger
from typing import Dict, List, Optional

from ..utils import Command

logger = getLogger(__name__)


class IpmiSel(Command):
    """Command line tool for ipmi sel."""

    prefix = ""
    command = "ipmi-sel"

    def get_sel_entries(self, time_range: int) -> Optional[List[Dict[str, str]]]:
        """Get SEL entries along with state.

        :param time_range int: Time in seconds, to determine from how far back the SEL
        entries should be read.
        Returns:
            sel_entries: a list of dictionaries containing sel_sentries, or []
        """
        result = self("--output-event-state --interpret-oem-data --entity-sensor-names")
        if result.error:
            logger.error(result.error)
            return None

        oldest_log_time = datetime.datetime.now() - datetime.timedelta(seconds=time_range)

        raw_sel_data = result.data.strip().split("\n")
        sel_entries = []
        sel_data_fields = ["ID", "Date", "Time", "Name", "Type", "State", "Event"]
        for sel_item in raw_sel_data[1:]:
            sel_item_values = sel_item.split("|")
            sel_item_values = [entry.strip() for entry in sel_item_values]
            sel_item_dict = dict(zip(sel_data_fields, sel_item_values))
            if sel_item_dict["Date"] == "PostInit":
                sel_entries.append(sel_item_dict)
            else:
                sel_item_datetime_str = sel_item_dict["Date"] + sel_item_dict["Time"]
                sel_item_datetime = datetime.datetime.strptime(
                    sel_item_datetime_str, "%b-%d-%Y%H:%M:%S"
                )
                if sel_item_datetime > oldest_log_time:
                    sel_entries.append(sel_item_dict)
        return sel_entries
