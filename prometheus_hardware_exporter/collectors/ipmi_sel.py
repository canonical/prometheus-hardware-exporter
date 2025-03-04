"""IPMI SEL metrics collector."""

import datetime
import threading
import time
from logging import getLogger
from typing import Dict, List, Optional

from ..config import Config
from ..utils import Command

logger = getLogger(__name__)


class IpmiSel(Command):
    """Command line tool for ipmi sel."""

    prefix = ""
    command = "ipmi-sel"

    def __init__(self, config: Config) -> None:
        """Initialize the IpmiSel class."""
        super().__init__(config)
        self.config.collect_timeout = None
        self._cache: Optional[List[Dict[str, str]]] = []
        self._lock = threading.Lock()
        self._cache_timestamp = datetime.datetime.now().timestamp()
        self._update_thread: Optional[threading.Thread] = None

    def _update_cache(self) -> None:
        """Background thread function to update SEL cache periodically."""
        # --sdr-cache-recreate is required to automatically recreate the SDR cache in case it is
        # out of date or invalid. Without this, the service will stop getting ipmi-sel data if the
        # cache is out of date.
        while True:
            result = self(
                (
                    "--sdr-cache-recreate --output-event-state "
                    "--interpret-oem-data --entity-sensor-names"
                )
            )

            if not result.error:
                raw_sel_data = result.data.strip().split("\n")
                sel_data_fields = ["ID", "Date", "Time", "Name", "Type", "State", "Event"]
                sel_entries = []
                for sel_item in raw_sel_data[1:]:
                    sel_item_values = [entry.strip() for entry in sel_item.split("|")]
                    sel_item_dict = dict(zip(sel_data_fields, sel_item_values))
                    sel_entries.append(sel_item_dict)

                with self._lock:
                    self._cache = sel_entries
            else:
                logger.error("Failed to fetch SEL entries: %s", result.error)
                self._cache = None

            self._cache_timestamp = datetime.datetime.now().timestamp()
            time.sleep(self.config.ipmi_sel_collect_interval)

    def _start_thread(self) -> None:
        """Start the background thread to update SEL cache."""
        self._update_thread = threading.Thread(target=self._update_cache, daemon=True)
        self._update_thread.start()

    def get_sel_entries(self, time_range: int) -> Optional[List[Dict[str, str]]]:
        """Get SEL entries along with state.

        :param time_range int: Time in seconds, to determine from how far back the SEL
        entries should be read.
        Returns:
            sel_entries: a list of dictionaries containing sel_sentries, or []
        """
        if self._update_thread is None or not self._update_thread.is_alive():
            self._start_thread()

        oldest_log_time = datetime.datetime.now() - datetime.timedelta(seconds=time_range)

        if (
            datetime.datetime.now().timestamp() - self._cache_timestamp
            > self.config.ipmi_sel_cache_ttl
        ):
            logger.error("IPMI SEL cache is expired.")
            return None

        with self._lock:
            if self._cache is None:
                return None
            return [
                entry
                for entry in self._cache
                if entry["Date"] == "PostInit"
                or (
                    datetime.datetime.strptime(entry["Date"] + entry["Time"], "%b-%d-%Y%H:%M:%S")
                    > oldest_log_time
                )
            ]
