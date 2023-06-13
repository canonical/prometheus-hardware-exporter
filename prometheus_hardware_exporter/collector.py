"""Module for a collection of hardware collecters."""

from logging import getLogger
from typing import Dict, List

from prometheus_client.metrics_core import GaugeMetricFamily, InfoMetricFamily

from .collectors.sasircu import LSISASCollectorHelper, Sasircu
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


class LSISASControllerCollector(BlockingCollector):
    """Collector for LSI SAS controllers."""

    def __init__(self, version: int) -> None:
        """Initialize the collector."""
        self.version = version
        self.sasircu = Sasircu(version)
        self.lsi_sas_helper = LSISASCollectorHelper()
        super().__init__()

    @property
    def specifications(self) -> List[Specification]:
        """Define LSI SAS metric specs."""
        return [
            Specification(
                name=f"lsi_sas_{self.version}_controllers",
                documentation="Number of LSI SAS-{self.version} controllers",
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_ir_volumes",
                documentation="Number of IR volumes",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_ready_ir_volumes",
                documentation="Number of ready IR volumes",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_unready_ir_volumes",
                documentation="Number of unready IR volumes",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_ir_volume",  # will append "_info" internally
                documentation="Shows the information about the integrated RAID volume",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_physical_devices",
                documentation="Number of physical devices",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_ready_physical_devices",
                documentation="Number of ready physical devices",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_unready_physical_devices",
                documentation="Number of unready physical devices",
                labels=["controller_id"],
                metric_class=GaugeMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_physical_device",  # will append "_info" internally
                documentation="Shows the information about the physical device",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name=f"lsi_sas_{self.version}_enclosure",  # will append "_info" internally
                documentation="Show the information about the enclosure",
                metric_class=InfoMetricFamily,
            ),
            Specification(
                name=f"sas{self.version}ircu_command_success",
                documentation="Indicates if the command is successful or not",
                metric_class=GaugeMetricFamily,
            ),
        ]

    def fetch(self) -> List[Payload]:
        """Load the LSI SAS controllers related information."""
        adapters = self.sasircu.get_adapters()
        all_information = [(idx, self.sasircu.get_all_information(idx)) for idx in adapters]

        if not all([adapters, all_information]):
            logger.error(
                "Failed to get LSI SAS-%d controller information using %s",
                self.version,
                self.sasircu.command,
            )
            return [Payload(name=f"sas{self.version}ircu_command_success", value=0.0)]

        payloads = [
            Payload(
                name=f"lsi_sas_{self.version}_controllers",
                value=len(adapters),
            ),
            Payload(
                name=f"sas{self.version}ircu_command_success",
                value=1.0,
            ),
        ]

        for idx, info in all_information:
            # Add integrated RAID volume metrics
            ir_volumes = self.lsi_sas_helper.extract_ir_volumes(idx, info)
            ir_volume_state_counts = self.lsi_sas_helper.count_ir_volume_state(
                ir_volumes, {"Okay (OKY)"}
            )
            payloads.extend(
                [
                    Payload(
                        name=f"lsi_sas_{self.version}_ir_volume",
                        value=ir_volume,
                    )
                    for ir_volume in ir_volumes
                ]
            )
            payloads.extend(
                [
                    Payload(
                        name=f"lsi_sas_{self.version}_ir_volumes",
                        labels=[idx],
                        value=ir_volume_state_counts[0],
                    ),
                    Payload(
                        name=f"lsi_sas_{self.version}_ready_ir_volumes",
                        labels=[idx],
                        value=ir_volume_state_counts[1],
                    ),
                    Payload(
                        name=f"lsi_sas_{self.version}_unready_ir_volumes",
                        labels=[idx],
                        value=ir_volume_state_counts[2],
                    ),
                ]
            )

            # Add physical disk metrics
            physical_disks = self.lsi_sas_helper.extract_physical_disks(idx, info)
            physical_disks_state_counts = self.lsi_sas_helper.count_physical_disk_state(
                physical_disks, {"Ready (RDY)", "Optimal (OPT)"}
            )
            payloads.extend(
                [
                    Payload(name=f"lsi_sas_{self.version}_physical_device", value=ir_volume)
                    for ir_volume in ir_volumes
                ]
            )
            payloads.extend(
                [
                    Payload(
                        name=f"lsi_sas_{self.version}_physical_devices",
                        labels=[idx],
                        value=physical_disks_state_counts[0],
                    ),
                    Payload(
                        name=f"lsi_sas_{self.version}_ready_physical_devices",
                        labels=[idx],
                        value=physical_disks_state_counts[1],
                    ),
                    Payload(
                        name=f"lsi_sas_{self.version}_unready_physical_devices",
                        labels=[idx],
                        value=physical_disks_state_counts[2],
                    ),
                ]
            )

            # Add enclosure metrics
            payloads.extend(
                [
                    Payload(name=f"lsi_sas_{self.version}_enclosure", value=enclosure)
                    for enclosure in self.lsi_sas_helper.extract_enclosures(idx, info)
                ]
            )
        return payloads

    def process(self, payloads: List[Payload], datastore: Dict[str, Payload]) -> List[Payload]:
        """Process the payload if needed."""
        return payloads
