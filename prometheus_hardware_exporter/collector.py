"""Module for a collection of hardware collecters."""

from logging import getLogger
from typing import Dict, List

from prometheus_client.metrics_core import GaugeMetricFamily, InfoMetricFamily

from .collectors.sasircu import Sasircu
from .collectors.storcli import StorCLI
from .core import BlockingCollector, Payload, Specification

logger = getLogger(__name__)


class MegaRAIDCollector(BlockingCollector):
    """Collector for MegaRAID controller."""

    storcli = StorCLI()

    @property
    def specifications(self) -> List[Specification]:
        """Define MegaRAID metric specs."""
        return [
            Specification(
                name="megaraid_controllers",
                documentation="Total number of controllers",
                labels=["hostname"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="megaraid_virtual_drive",
                documentation="Number of virtual drives",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="megaraid_virtual_drive_state",
                documentation="Indicates the state of virtual drive",
                labels=["controller_id", "virtual_drive_id", "state"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="megaraid_virtual_drive_cache_policy",
                documentation="Indicates the cache policy of virtual drive",
                labels=["controller_id", "virtual_drive_id", "cache_policy"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="storcli_command_success",
                documentation="Indicates the if command is successful or not",
                labels=[],
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load the MegaRAID related information."""
        controller_payload = self.storcli.get_controllers()
        virtual_drives_payload = self.storcli.get_all_virtual_drives()

        if not all([controller_payload, virtual_drives_payload]):
            logger.error(
                "Failed to get MegaRAID controller information using %s", self.storcli.command
            )
            return [
                Payload(
                    name="storcli_command_success",
                    labels=[],
                    value=0.0,
                )
            ]

        payloads = [
            Payload(
                name="megaraid_controllers",
                labels=[controller_payload["hostname"]],
                value=controller_payload["count"],
            ),
            Payload(
                name="storcli_command_success",
                labels=[],
                value=1.0,
            ),
        ]
        for ctrl_id, vds_payload in virtual_drives_payload.items():
            payloads.append(
                Payload(
                    name="megaraid_virtual_drive",
                    labels=[str(ctrl_id)],
                    value=len(vds_payload),
                )
            )
            for vd_payload in vds_payload:
                payloads.append(
                    Payload(
                        name="megaraid_virtual_drive_state",
                        labels=[vd_payload["DG"], vd_payload["VD"], vd_payload["state"]],
                        value=1.0,
                    )
                )
                payloads.append(
                    Payload(
                        name="megaraid_virtual_drive_cache_policy",
                        labels=[vd_payload["DG"], vd_payload["VD"], vd_payload["cache"]],
                        value=1.0,
                    )
                )
        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads


class LSISAS2ControllerCollector(BlockingCollector):
    """Collector for LSI SAS-2 controllers."""

    sas2ircu = Sasircu(2)

    @property
    def specifications(self) -> List[Specification]:
        """Define LSI SAS-2 metric specs."""
        return [
            Specification(
                name="lsi_sas_2_controllers",
                documentation="Number of controllers",
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="lsi_sas_2_ir_volumes",
                documentation="Number of integrated RAID volumes",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="lsi_sas_2_ir_volume",  # will append "_info" internally
                documentation="Shows the information about the integrated RAID volume",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name="lsi_sas_2_physical_devices",
                documentation="Number of physical devices",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="lsi_sas_2_physical_device",  # will append "_info" internally
                documentation="Shows the information about the physical device",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name="lsi_sas_2_enclosure",  # will append "_info" internally
                documentation="Show the information about the enclosure",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name="sas2ircu_command_success",
                documentation="Indicates if the command is successful or not",
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load the LSI SAS-2 controllers related information."""
        adapters = self.sas2ircu.get_adapters()
        all_information = [(idx, self.sas2ircu.get_all_information(idx)) for idx in adapters]

        if not all([adapters, all_information]):
            logger.error(
                "Failed to get LSI SAS-2 controller information using %s", self.sas2ircu.command
            )
            return [
                Payload(
                    name="sas2ircu_command_success",
                    value=0.0,
                )
            ]

        payloads = [
            Payload(
                name="lsi_sas_2_controllers",
                value=len(adapters),
            ),
            Payload(
                name="sas2ircu_command_success",
                value=1.0,
            ),
        ]

        for idx, info in all_information:
            # Add integrated RAID volume metrics
            if info["ir_volumes"]:
                payloads.append(
                    Payload(
                        name="lsi_sas_2_ir_volumes",
                        value=len(info["ir_volumes"]),
                        labels=[str(idx)],
                    )
                )
                for volume in info["ir_volumes"].values():
                    payloads.append(
                        Payload(
                            name="lsi_sas_2_ir_volume",
                            value={
                                "controller_id": idx,
                                "volume_id": volume["Volume ID"],
                                "status": volume["Status of volume"],
                                "size_mb": volume["Size (in MB)"],
                                "boot": volume["Boot"],
                                "raid_level": volume["RAID level"],
                                "hard_disk": ",".join(volume["Physical hard disks"].values()),
                            },
                        )
                    )
            # Add physical disk metrics
            if info["physical_disks"]:
                payloads.append(
                    Payload(
                        name="lsi_sas_2_physical_devices",
                        value=len(info["physical_disks"]),
                        labels=[str(idx)],
                    )
                )
                for disk in info["physical_disks"].values():
                    payloads.append(
                        Payload(
                            name="lsi_sas_2_physical_device",
                            value={
                                "controller_id": idx,
                                "enclosure_id": disk["Enclosure #"],
                                "slot_id": disk["Slot #"],
                                "size_mb_sectors": disk["Size (in MB)/(in sectors)"],
                                "drive_type": disk["Drive Type"],
                                "protocol": disk["Protocol"],
                                "state": disk["State"],
                            },
                        )
                    )
            # Add enclosure metrics
            if info["enclosures"]:
                for encl in info["enclosures"].values():
                    payloads.append(
                        Payload(
                            name="lsi_sas_2_enclosure",
                            value={
                                "controller_id": idx,
                                "enclosure_id": encl["Enclosure#"],
                                "num_slots": encl["Numslots"],
                                "start_slot": encl["StartSlot"],
                            },
                        )
                    )
        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads


class LSISAS3ControllerCollector(BlockingCollector):
    """Collector for LSI SAS-3 controllers."""

    sas3ircu = Sasircu(3)

    @property
    def specifications(self) -> List[Specification]:
        """Define LSI SAS-3 metric specs."""
        return [
            Specification(
                name="lsi_sas_3_controllers",
                documentation="Number of controllers",
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="lsi_sas_3_ir_volumes",
                documentation="Number of integrated RAID volumes",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="lsi_sas_3_ir_volume",  # will append "_info" internally
                documentation="Shows the information about the integrated RAID volume",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name="lsi_sas_3_physical_devices",
                documentation="Number of physical devices",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name="lsi_sas_3_physical_device",  # will append "_info" internally
                documentation="Shows the information about the physical device",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name="lsi_sas_3_enclosure",  # will append "_info" internally
                documentation="Show the information about the enclosure",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name="sas3ircu_command_success",
                documentation="Indicates if the command is successful or not",
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load the LSI SAS-3 controllers related information."""
        adapters = self.sas3ircu.get_adapters()
        all_information = [(idx, self.sas3ircu.get_all_information(idx)) for idx in adapters]

        if not all([adapters, all_information]):
            logger.error(
                "Failed to get LSI SAS-3 controller information using %s", self.sas3ircu.command
            )
            return [
                Payload(
                    name="sas3ircu_command_success",
                    value=0.0,
                )
            ]

        payloads = [
            Payload(
                name="lsi_sas_3_controllers",
                value=len(adapters),
            ),
            Payload(
                name="sas3ircu_command_success",
                value=1.0,
            ),
        ]

        for idx, info in all_information:
            # Add integrated RAID volume metrics
            if info["ir_volumes"]:
                payloads.append(
                    Payload(
                        name="lsi_sas_3_ir_volumes",
                        value=len(info["ir_volumes"]),
                        labels=[str(idx)],
                    )
                )
                for volume in info["ir_volumes"].values():
                    payloads.append(
                        Payload(
                            name="lsi_sas_3_ir_volume",
                            value={
                                "controller_id": idx,
                                "volume_id": volume["Volume ID"],
                                "status": volume["Status of volume"],
                                "size_mb": volume["Size (in MB)"],
                                "boot": volume["Boot"],
                                "raid_level": volume["RAID level"],
                                "hard_disk": ",".join(volume["Physical hard disks"].values()),
                            },
                        )
                    )
            # Add physical disk metrics
            if info["physical_disks"]:
                payloads.append(
                    Payload(
                        name="lsi_sas_3_physical_devices",
                        value=len(info["physical_disks"]),
                        labels=[str(idx)],
                    )
                )
                for disk in info["physical_disks"].values():
                    payloads.append(
                        Payload(
                            name="lsi_sas_3_physical_device",
                            value={
                                "controller_id": idx,
                                "enclosure_id": disk["Enclosure #"],
                                "slot_id": disk["Slot #"],
                                "size_mb_sectors": disk["Size (in MB)/(in sectors)"],
                                "drive_type": disk["Drive Type"],
                                "protocol": disk["Protocol"],
                                "state": disk["State"],
                            },
                        )
                    )
            # Add enclosure metrics
            if info["enclosures"]:
                for encl in info["enclosures"].values():
                    payloads.append(
                        Payload(
                            name="lsi_sas_3_enclosure",
                            value={
                                "controller_id": idx,
                                "enclosure_id": encl["Enclosure#"],
                                "num_slots": encl["Numslots"],
                                "start_slot": encl["StartSlot"],
                            },
                        )
                    )
        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads
