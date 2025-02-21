"""IPMI SEL metrics collector."""

import datetime
import os
from logging import getLogger
from typing import Dict, List, Optional

from crontab import CronTab

from prometheus_hardware_exporter.config import Config

from ..utils import Command, Result

logger = getLogger(__name__)


class IpmiSel(Command):
    """Ipmi sel cronjob handler."""

    prefix = ""
    command = "ipmi-sel"
    job_name = "ipmi_sel_job"
    job_output_file = "/tmp/ipmi_sel_output.txt"

    def __init__(self, config: Config) -> None:
        """Initialize the IpmiSel class and check if the ipmi-sel command is installed."""
        super().__init__(config)
        result = self()
        if result.error:
            logger.error(result.error)
            return

        self.cron = CronTab(user=True)
        self.setup_cron_job(config.ipmi_sel_cronjob_interval)

    def __del__(self) -> None:
        """Remove the cron job."""
        self.cron.remove_all(comment=self.job_name)
        self.cron.write()
        logger.info("Removed the cron job %s.", self.job_name)

    def setup_cron_job(self, interval: int) -> None:
        """Set up a cron job to run the ipmi-sel command at a given interval.

        :param interval: The interval in minutes at which the cron job should run.
        """
        # --sdr-cache-recreate is required to automatically recreate the SDR cache in case it is
        # out of date or invalid. Without this, the service will stop getting ipmi-sel data if the
        # cache is out of date.
        cronjob_command = (
            f"{self.command} --sdr-cache-recreate --output-event-state "
            f"--interpret-oem-data --entity-sensor-names > {self.job_output_file}"
        )

        job_exists = any(job.comment == self.job_name for job in self.cron)

        if not job_exists:
            job = self.cron.new(command=cronjob_command, comment=self.job_name)
            job.minute.every(interval)
            self.cron.write()
            logger.info(
                "Created a new cron job to run %s every %d minutes.", self.command, interval
            )

    def get_sel_entries(self, time_range: int) -> Optional[List[Dict[str, str]]]:
        """Get SEL entries along with state.

        :param time_range int: Time in seconds, to determine from how far back the SEL
        entries should be read.
        Returns:
            sel_entries: a list of dictionaries containing sel_sentries, or []
        """
        if not os.path.exists(self.job_output_file):
            logger.warning("IPMI SEL output file not found.")
            return None

        with open(self.job_output_file, "r", encoding="utf-8") as file:
            result = Result(data=file.read())
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
